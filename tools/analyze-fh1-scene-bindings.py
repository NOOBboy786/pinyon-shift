"""Analyze bounded FH1 scene snapshots; never authorize draw suppression."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


MARKER = "FH1 scene binding "
BINDINGS = ("vertex_shader", "pixel_shader", "attachment",
            "pipeline", "dynamic", "operation", "hazards", "flags",
            "index_base", "index_count", "index_length", "textures", "vertices")


def decode_commands(encoded):
    if len(encoded) % 8:
        raise ValueError("partial command word")
    words = [int(encoded[i:i + 8], 16) for i in range(0, len(encoded), 8)]
    packets = []
    offset = 0
    while offset < len(words):
        header = words[offset]
        kind = header >> 30
        count = (0 if header == 0 or kind == 2 else
                 2 if kind == 1 else ((header >> 16) & 0x3FFF) + 1)
        end = offset + 1 + count
        if end > len(words):
            raise ValueError(f"truncated command at byte {offset * 4}")
        payload = words[offset + 1:end]
        writes = []
        loads = []
        opcode = (header >> 8) & 0x7F if kind == 3 else None
        if header and kind == 0:
            base = header & 0x7FFF
            writes = [(base if header & 0x8000 else base + i, value)
                      for i, value in enumerate(payload)]
        elif kind == 1:
            writes = [(header & 0x7FF, payload[0]),
                      ((header >> 11) & 0x7FF, payload[1])]
        elif opcode in (0x2D, 0x2F):
            if len(payload) < (1 if opcode == 0x2D else 3):
                raise ValueError('truncated constant command')
            offset_type = payload[0 if opcode == 0x2D else 1]
            bank = (offset_type >> 16) & 0xFF
            if bank > 4:
                raise ValueError('unknown constant bank')
            register = (0x4000, 0x4800, 0x4900, 0x4908, 0x2000)[bank] + (offset_type & 0x7FF)
            if opcode == 0x2D:
                writes = [(register + i, value) for i, value in enumerate(payload[1:])]
            else:
                loads.append(dict(kind='constants', address=payload[0] & 0x3FFFFFFF,
                                  register=register, words=payload[2] & 0xFFF))
        elif opcode == 0x27:
            if len(payload) != 2 or payload[1] >> 16 or (payload[0] & 3) > 1:
                raise ValueError('unsupported shader load')
            loads.append(dict(kind='shader', stage='pixel' if payload[0] & 3 else 'vertex',
                              address=payload[0] & ~3, words=payload[1] & 0xFFFF))
        packets.append({"offset": offset * 4, "type": kind,
                        "header": f"{header:08X}",
                        "opcode": opcode,
                        "predicated": bool(header & 1) if kind == 3 else False,
                        "payload": [f"{word:08X}" for word in payload],
                        "external_loads": loads,
                        "direct_register_writes": [
                            {"register": register, "value": f"{value:08X}"}
                            for register, value in writes],
                        # Every scratch write may reach guest memory through
                        # SCRATCH_UMSK / SCRATCH_ADDR, even repeated values.
                        # Keep the order; final register values are insufficient.
                        "scratch_writebacks": [
                            {"scratch": register - 0x578, "value": f"{value:08X}"}
                            for register, value in writes if 0x578 <= register <= 0x57F]})
        offset = end
    return packets


def analyze(records, producers=()):
    if not records:
        raise ValueError("no FH1 scene binding records")
    previous = None
    runs = {"same_bindings": [], "same_bindings_and_constants": []}
    constants = defaultdict(set)
    instance_pairs = Counter()
    previous_constants = {}
    producer_objects = defaultdict(set)
    for producer in producers:
        producer_objects[(producer["target"] & 0x1FFFFFFF,
                          (producer["words"] & 0xFFFFF) * 4)].add(producer["object"])
    buffers = Counter()
    input_groups = defaultdict(list)
    unhashed_command_records = 0
    side_effect_states = Counter()
    missing_side_effect_states = 0
    for record in records:
        if all(k in record for k in ('scratch_mask', 'scratch_address', 'bin_mask', 'bin_select')):
            side_effect_states[(record['scratch_mask'], record['scratch_address'],
                                record['bin_mask'], record['bin_select'])] += 1
        else:
            missing_side_effect_states += 1
        if previous and record["sequence"] <= previous["sequence"]:
            raise ValueError("draw sequences must increase within one session")
        adjacent = previous is not None and (
            record["frame"] == previous["frame"] and
            record["sequence"] == previous["sequence"] + 1
        )
        same = adjacent and all(record[k] == previous[k] for k in BINDINGS)
        # Count only runs without observed hazards. Other GPU activity and
        # resource contents still require separate validation for an executor.
        same = same and record["hazards"] == 0
        for name, match in (
            ("same_bindings", same),
            ("same_bindings_and_constants",
             same and record["constants"] == previous["constants"]),
        ):
            if match:
                runs[name][-1] += 1
            else:
                runs[name].append(1)
        current_constants = {}
        for item in record["constants"].split(";"):
            if item:
                register, value = item.split(":", 1)
                constants[register].add(value)
                current_constants[register] = value
        if adjacent and previous["vertex_shader"] == "8D8A197476841A9A" and \
                record["vertex_shader"] == "AD2C355A6BE1EE87":
            registers = (16896, 16900, 16904, 16908, 16944, 16948, 16952)
            matched = all(str(r) in current_constants and
                          current_constants[str(r)] == previous_constants.get(str(r))
                          for r in registers)
            instance_pairs["matching_transform" if matched else "different_or_missing_transform"] += 1
        previous_constants = current_constants
        if "command_buffer" in record:
            buffers[(record["command_buffer"], record["command_bytes"])] += 1
        if record.get('command_hash') not in (None, '0000000000000000'):
            input_groups[(record['command_buffer'], record['command_bytes'],
                          record.get('draw_end_offset'), record['vertex_shader'],
                          record['pixel_shader'])].append(record)
        else:
            unhashed_command_records += 1
        previous = record
    return {
        "records": len(records),
        "unhashed_command_records": unhashed_command_records,
        # Stable command bytes do not imply stable draw inputs. These are
        # observed descriptor/constant states, not resource-content versions.
        "command_input_variation": [
            dict(address=address, bytes=size, draw_end_offset=offset,
                 vertex_shader=vertex, pixel_shader=pixel, records=len(group),
                 observed_states={field: len({r[field] for r in group})
                                  for field in ('command_hash', 'constants',
                                                'textures', 'vertices', 'index_base')})
            for (address, size, offset, vertex, pixel), group in input_groups.items()
        ],
        "missing_side_effect_states": missing_side_effect_states,
        "draw_time_side_effect_states": [
            dict(scratch_mask=mask, scratch_address=address, bin_mask=bin_mask,
                 bin_select=selection, records=count)
            for (mask, address, bin_mask, selection), count in side_effect_states.most_common()
        ],
        "frames": dict(Counter(r["frame"] for r in records)),
        "unique_values": {k: len({r[k] for r in records})
                          for k in (*BINDINGS, "constants")},
        "runs": {name: {"count": len(lengths), "maximum": max(lengths),
                        "draws_in_multi_draw_runs": sum(n for n in lengths if n > 1)}
                 for name, lengths in runs.items()},
        "varying_constants": {k: len(v) for k, v in constants.items() if len(v) > 1},
        "blended_lit_then_target_pairs": dict(instance_pairs),
        "command_buffers": [
            {"address": address, "bytes": size, "draws": count,
             "observed_producer_objects": sorted(producer_objects[(address, size)])}
            for (address, size), count in buffers.most_common()
        ],
        "suppression_authorized": False,
    }


def select_scene_packets(packets, selection):
    """Resolve this family's bin predicates; retain every executed side effect.

    The family initializes both mask halves before using predicates and never
    changes selection. Reject anything outside that proven command vocabulary.
    Returned packets are an offline submission recipe, not suppression approval.
    """
    mask = 0
    initialized = 0
    selected = []
    for packet in packets:
        opcode = packet['opcode']
        if packet['type'] == 3 and opcode not in (0x60, 0x61, 0x2D, 0x27, 0x2F, 0x22):
            raise ValueError('unsupported scene command')
        if packet['predicated']:
            if initialized != 3:
                raise ValueError('predicate depends on unknown incoming mask')
            if not mask & selection:
                continue
        if opcode in (0x60, 0x61):
            if len(packet['payload']) != 1:
                raise ValueError('invalid bin mask command length')
            shift = 0 if opcode == 0x60 else 32
            mask = (mask & ~(0xFFFFFFFF << shift)) | (int(packet['payload'][0], 16) << shift)
            initialized |= 1 if shift == 0 else 2
        selected.append(packet)
    if initialized != 3:
        raise ValueError('scene family does not initialize its bin mask')
    return selected, mask


def self_test():
    external = decode_commands('C0022F0012345678000003F000000010'
                               'C00127001234568100000027')
    assert external[0]['external_loads'] == [dict(
        kind='constants', address=0x12345678, register=0x43F0, words=16)]
    assert external[1]['external_loads'] == [dict(
        kind='shader', stage='pixel', address=0x12345680, words=0x27)]
    assert decode_commands('C0012D000004008000000123')[0]['direct_register_writes'] == [
        dict(register=0x2080, value='00000123')]
    assert len(decode_commands("0000000080000000C0013F000000100000000004")) == 3
    predicates = decode_commands('C000610000000000C00060000000000C'
                                 'C0002D0100040080C000600000000030'
                                 'C0002D0100040080')
    selected, mask = select_scene_packets(predicates, 0xC)
    assert [p['offset'] for p in selected] == [0, 8, 16, 24] and mask == 0x30
    assert len(select_scene_packets(predicates, 0)[0]) == 3
    try:
        select_scene_packets(predicates[2:], 0xC)
    except ValueError:
        pass
    else:
        raise AssertionError('unknown incoming predicate accepted')
    repeated = decode_commands("0002857E000000110000002200000011")[0]
    assert repeated["scratch_writebacks"] == [
        {"scratch": 6, "value": value} for value in ("00000011", "00000022", "00000011")]
    sequential = decode_commands("0001057E0000001100000022")[0]
    assert [w["scratch"] for w in sequential["scratch_writebacks"]] == [6, 7]
    header = 0x40000000 | (0x57F << 11) | 0x578
    assert [w["scratch"] for w in decode_commands(
        f"{header:08X}0000001100000022")[0]["scratch_writebacks"]] == [0, 7]
    assert decode_commands("C003220100000000000000000000000000000000")[0]["predicated"]
    assert not decode_commands("0000057F00000011")[0]["predicated"]
    try:
        decode_commands("C0013F0000001000")
    except ValueError:
        pass
    else:
        raise AssertionError("truncated command accepted")
    base = dict.fromkeys(BINDINGS, 0)
    a = dict(base, frame=1, sequence=1, constants="1:AAAA;")
    b = dict(a, sequence=2, constants="1:BBBB;")
    gap = dict(b, sequence=4)
    frame = dict(b, frame=2, sequence=5)
    result = analyze([a, b, gap, frame])
    assert result["runs"]["same_bindings"]["maximum"] == 2
    assert result["runs"]["same_bindings_and_constants"]["maximum"] == 1
    assert result["varying_constants"] == {"1": 2}
    assert result['missing_side_effect_states'] == 4
    sampled = dict(a, command_buffer=4096, command_bytes=32,
                   draw_end_offset=24, command_hash='1111111111111111')
    changed = dict(sampled, sequence=2, constants='1:BBBB;')
    missing = dict(sampled, sequence=3, command_hash='0000000000000000')
    variation = analyze([sampled, changed, missing])
    assert variation['unhashed_command_records'] == 1
    assert variation['command_input_variation'][0]['observed_states'] == dict(
        command_hash=1, constants=2, textures=1, vertices=1, index_base=1)
    assert len(analyze([sampled, dict(changed, draw_end_offset=28)])[
        'command_input_variation']) == 2
    live = dict(a, scratch_mask=0xC0, scratch_address=0x1000,
                bin_mask='0000000000000001', bin_select='0000000000000001')
    state = analyze([live, b])
    assert state['missing_side_effect_states'] == 1
    assert state['draw_time_side_effect_states'] == [dict(
        scratch_mask=0xC0, scratch_address=0x1000,
        bin_mask='0000000000000001', bin_select='0000000000000001', records=1)]
    hazard = dict(b, hazards=1)
    assert analyze([dict(a, hazards=1), hazard])["runs"]["same_bindings"]["maximum"] == 1
    transforms = "".join(f"{r}:ABCD;" for r in
                         (16896, 16900, 16904, 16908, 16944, 16948, 16952))
    pair = [dict(a, vertex_shader="8D8A197476841A9A", constants=transforms),
            dict(b, vertex_shader="AD2C355A6BE1EE87", constants=transforms)]
    assert analyze(pair)["blended_lit_then_target_pairs"] == {"matching_transform": 1}
    pair[1]["constants"] = ""
    assert analyze(pair)["blended_lit_then_target_pairs"] == {"different_or_missing_transform": 1}
    sample = dict(a, command_buffer=0x1000, command_bytes=16)
    producers = [{"object": 1, "target": 0xA0001000, "words": 4},
                 {"object": 2, "target": 0x1000, "words": 8}]
    assert analyze([sample], producers)["command_buffers"][0]["observed_producer_objects"] == [1]
    try:
        analyze([a, a])
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate sequences accepted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        if args.log is None:
            parser.error("a single-session runtime log is required")
        text = args.log.read_text(encoding="utf-8")
        records = [json.loads(line.split(MARKER, 1)[1]) for line in text.splitlines()
                   if MARKER + "{" in line]
        producers = [json.loads(line.split("FH1 scene producer ", 1)[1])
                     for line in text.splitlines() if "FH1 scene producer {" in line]
        result = analyze(records, producers)
        result["record_limit_reached"] = "FH1 scene binding record limit reached" in text
        result["producer_record_limit_reached"] = "FH1 scene producer record limit reached" in text
        commands = [json.loads(line.split("FH1 scene commands ", 1)[1])
                    for line in text.splitlines() if "FH1 scene commands {" in line]
        result["command_snapshots"] = [
            {"hash": c["hash"], "address": c["address"],
             "packets": decode_commands(c["words"])} for c in commands
        ]
        result['scene_predicate_variants'] = []
        for snapshot in result['command_snapshots']:
            selections = sorted({r['bin_select'] for r in records
                                 if r.get('command_hash') == snapshot['hash']
                                 and 'bin_select' in r})
            for selection in selections:
                selected, mask = select_scene_packets(snapshot['packets'], int(selection, 16))
                shaders = {}
                draw_bindings = []
                for packet in selected:
                    for load in packet['external_loads']:
                        if load['kind'] == 'shader':
                            shaders[load['stage']] = load
                    if packet['opcode'] == 0x22:
                        draw_bindings.append(dict(offset=packet['offset'], shaders=dict(shaders)))
                result['scene_predicate_variants'].append(dict(
                    command_hash=snapshot['hash'], bin_select=selection,
                    executed_packet_offsets=[p['offset'] for p in selected],
                    draw_offsets=[p['offset'] for p in selected if p['opcode'] == 0x22],
                    draw_shader_loads=draw_bindings,
                    skipped_packet_offsets=[p['offset'] for p in snapshot['packets'] if p not in selected],
                    final_bin_mask=f'{mask:016X}'))
        print(json.dumps(result, indent=2))
