"""Rank one FH1 corpus snapshot by draw coverage, not GPU cost or native status."""

import argparse
import json
from pathlib import Path


def rank(corpus):
    if corpus.get("schema") != "pinyon-shift.fh1-gpu-corpus.v3":
        raise ValueError("expected an FH1 GPU corpus v3 snapshot")
    if corpus.get("overflow") != 0 or corpus.get("collisions") != 0:
        raise ValueError("corpus contains dropped or ambiguous draw identities")
    groups = {}
    identities = set()
    for entry in corpus["entries"]:
        if entry["identity"] in identities:
            raise ValueError("duplicate corpus identity; use one snapshot")
        identities.add(entry["identity"])
        if entry["kind"] != 1:
            continue
        count, indices = entry["count"], entry["index_count"]
        if type(count) is not int or count < 0 or type(indices) is not int or indices < 0:
            raise ValueError("draw counts must be nonnegative integers")
        key = entry["vertex_shader"], entry["pixel_shader"]
        group = groups.setdefault(key, {"draws": 0, "submitted_indices": 0, "pipelines": set()})
        group["draws"] += count
        group["submitted_indices"] += count * indices
        group["pipelines"].add(entry["pipeline_state"])
    rows = [dict(vertex_shader=vs, pixel_shader=ps, draws=g["draws"],
                 submitted_indices=g["submitted_indices"], pipelines=sorted(g["pipelines"]))
            for (vs, ps), g in groups.items()]
    rows.sort(key=lambda row: (-row["draws"], row["vertex_shader"], row["pixel_shader"]))
    return {"draws": sum(row["draws"] for row in rows), "pairs": rows}


def rank_families(corpus):
    """Independent sampled shader-pair inventory; never infer complete key coverage."""
    if corpus.get('schema') != 'pinyon-shift.fh1-gpu-corpus.v3':
        raise ValueError('expected an FH1 GPU corpus v3 snapshot')
    if 'shader_families' not in corpus:
        result = rank(corpus)  # Old snapshots still require complete detailed keys.
        return dict(result, source='execution_keys', status='complete_for_observed_draws',
                    observation_frame_stride=corpus.get('observation_frame_stride', 1))
    overflow = corpus.get('shader_family_overflow')
    if type(overflow) is not int or overflow < 0:
        raise ValueError('invalid shader family overflow')
    pairs, seen = [], set()
    for entry in corpus['shader_families']:
        key = entry['vertex_shader'], entry['pixel_shader']
        if any(not isinstance(shader, str) or len(shader) != 16 or
               any(c not in '0123456789abcdefABCDEF' for c in shader) for shader in key):
            raise ValueError('invalid shader hash')
        key = tuple(shader.upper() for shader in key)
        if key in seen:
            raise ValueError('duplicate shader family')
        seen.add(key)
        count, first, last = (entry[k] for k in ('count', 'first_frame', 'last_frame'))
        if any(type(v) is not int or v < 0 for v in (count, first, last)) or last < first:
            raise ValueError('invalid shader family counts or frames')
        pairs.append(dict(vertex_shader=key[0], pixel_shader=key[1], draws=count,
                          first_frame=first, last_frame=last))
    pairs.sort(key=lambda row: (-row['draws'], row['vertex_shader'], row['pixel_shader']))
    return dict(source='shader_families',
                status='incomplete' if overflow else 'complete_for_observed_draws',
                overflow=overflow, observation_frame_stride=corpus.get('observation_frame_stride', 1),
                draws=sum(row['draws'] for row in pairs), pairs=pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument('--families', action='store_true', help='rank independent shader families')
    args = parser.parse_args()
    print(json.dumps((rank_families if args.families else rank)(
        json.loads(args.corpus.read_text(encoding="utf-8-sig"))), indent=2))


if __name__ == "__main__":
    main()
