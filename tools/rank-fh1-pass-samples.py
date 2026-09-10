"""Rank sampled FH1 pass spans in one session; never attribute mixed spans to a shader."""

import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fh1_runtime_log import session_lines


def rank(lines, first, last, session):
    if not 0 <= first <= last:
        raise ValueError('invalid frame range')
    records = {}
    for line in session_lines(lines, session):
        if 'FH1 V5 pass sample ' not in line:
            continue
        row = json.loads(line.split('FH1 V5 pass sample ', 1)[1])
        if not first <= row['frame'] <= last:
            continue
        key = row['submission'], row['record']
        if key in records and records[key] != row:
            raise ValueError('conflicting records; supply exactly one session')
        for field in ('frame', 'submission', 'record', 'draws', 'total_ns', 'draw_ns', 'resolve_ns'):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError('invalid timing record')
        if 'prepare_cpu_ns' in row and (type(row['prepare_cpu_ns']) is not int or row['prepare_cpu_ns'] < 0):
            raise ValueError('invalid preparation CPU time')
        recording_fields = ('recording_wall_ns', 'begin_submission', 'end_submission')
        if any(field in row for field in recording_fields):
            if not all(field in row and type(row[field]) is int and row[field] >= 0 for field in recording_fields):
                raise ValueError('incomplete or invalid recording interval')
            if not row['begin_submission'] <= row['end_submission'] <= row['submission']:
                raise ValueError('invalid recording submission order')
        records[key] = row
    frames = sorted({row['frame'] for row in records.values()})
    if not frames:
        raise ValueError('no sampled passes in selected frames')
    has_cpu = all('prepare_cpu_ns' in row for row in records.values())
    has_recording = all('recording_wall_ns' in row for row in records.values())
    groups = {}
    for row in records.values():
        group = groups.setdefault(row['family'], dict(family=row['family'], first_draw=row['first_draw'],
            occurrences=0, draws=0, total_ns=0, draw_ns=0, resolve_ns=0))
        if group['first_draw'] != row['first_draw']:
            raise ValueError('ambiguous family identity')
        if has_cpu:
            group['prepare_cpu_ns'] = group.get('prepare_cpu_ns', 0) + row['prepare_cpu_ns']
        if has_recording:
            group['recording_wall_ns'] = group.get('recording_wall_ns', 0) + row['recording_wall_ns']
            group['max_recording_wall_ns'] = max(group.get('max_recording_wall_ns', 0), row['recording_wall_ns'])
            group['spans_crossing_submissions'] = group.get('spans_crossing_submissions', 0) + (row['begin_submission'] != row['end_submission'])
        group['occurrences'] += 1
        for field in ('draws', 'total_ns', 'draw_ns', 'resolve_ns'):
            group[field] += row[field]
    result = sorted(groups.values(), key=lambda row: -row['total_ns'])
    for row in result:
        if has_cpu:
            row['prepare_cpu_ms_per_sampled_frame'] = row['prepare_cpu_ns'] / len(frames) / 1e6
        if has_recording:
            row['recording_wall_ms_per_sampled_frame'] = row['recording_wall_ns'] / len(frames) / 1e6
        row['ms_per_sampled_frame'] = row['total_ns'] / len(frames) / 1e6
        row['resolve_ms_per_sampled_frame'] = row['resolve_ns'] / len(frames) / 1e6
    frame_cpu = ({frame: sum(row['prepare_cpu_ns'] for row in records.values()
                             if row['frame'] == frame) / 1e6 for frame in frames}
                 if has_cpu else None)
    return dict(session=session, frames=frames, records=len(records), families=result,
                prepare_cpu_ms_by_frame=frame_cpu,
                scope='Observed pass spans only; missing/dropped samples and GPU work outside spans are excluded')


def self_test():
    def rank_test(lines, first, last):
        start = 'M2_EVENT ' + json.dumps(dict(event='logging.ready', session='test'))
        return rank([start, *lines], first, last, 'test')
    a = dict(frame=60, submission=1, record=0, family='A', first_draw='1',
             draws=2, total_ns=1000000, draw_ns=800000, resolve_ns=200000)
    b = dict(a, frame=120, submission=2, total_ns=3000000)
    c = dict(b, record=1, family='B', first_draw='2', total_ns=2000000)
    lines = ['FH1 V5 pass sample ' + json.dumps(row) for row in (a, b, c, a)]
    result = rank_test(lines, 60, 120)
    assert result['frames'] == [60, 120] and result['records'] == 3
    assert result['families'][0]['ms_per_sampled_frame'] == 2
    assert result['families'][1]['ms_per_sampled_frame'] == 1  # absent at frame 60
    assert rank_test(lines, 120, 120)['records'] == 2
    recorded = dict(a, recording_wall_ns=500000, begin_submission=0, end_submission=1)
    recorded_lines = ['FH1 V5 pass sample ' + json.dumps(recorded)]
    recorded_rank = rank_test(recorded_lines, 60, 60)['families'][0]
    assert recorded_rank['recording_wall_ms_per_sampled_frame'] == .5
    assert recorded_rank['spans_crossing_submissions'] == 1
    for bad in (dict(recorded, end_submission=2), dict(recorded, begin_submission=2),
                dict(recorded, recording_wall_ns=-1), dict(a, recording_wall_ns=1)):
        try:
            rank_test(['FH1 V5 pass sample ' + json.dumps(bad)], 60, 60)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid recording interval accepted')
    cpu_lines = ['FH1 V5 pass sample ' + json.dumps(dict(row, prepare_cpu_ns=value))
                 for row, value in ((a, 100000), (b, 300000), (c, 200000))]
    cpu = rank_test(cpu_lines, 60, 120)
    assert cpu['prepare_cpu_ms_by_frame'] == {60: .1, 120: .5}
    assert cpu['families'][0]['prepare_cpu_ms_per_sampled_frame'] == .2
    assert cpu['families'][1]['prepare_cpu_ms_per_sampled_frame'] == .1
    mixed = rank_test(cpu_lines[:1] + lines[1:3], 60, 120)
    assert all('prepare_cpu_ns' not in row for row in mixed['families'])
    invalid_cpu = ['FH1 V5 pass sample ' + json.dumps(dict(a, prepare_cpu_ns=-1))]
    for bad in ([], invalid_cpu, lines + ['FH1 V5 pass sample ' + json.dumps(dict(a, total_ns=2))]):
        try:
            rank_test(bad, 60, 120)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid input accepted')
    start = lambda name: 'M2_EVENT ' + json.dumps(dict(event='logging.ready', session=name))
    merged = [start('a'), *lines, start('b'), *cpu_lines]
    assert rank(merged, 60, 120, 'a')['prepare_cpu_ms_by_frame'] is None
    assert rank(merged, 60, 120, 'b')['prepare_cpu_ms_by_frame'] == {60: .1, 120: .5}
    for missing in ('missing', ''):
        try:
            rank(merged, 60, 120, missing)
        except ValueError:
            pass
        else:
            raise AssertionError('missing session accepted')
    print('pass-sample ranking and merged-session isolation checks passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path, nargs='?')
    parser.add_argument('--first-frame', type=int)
    parser.add_argument('--last-frame', type=int)
    parser.add_argument('--session')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        if args.log is None or not args.session or args.first_frame is None or args.last_frame is None or not 0 <= args.first_frame <= args.last_frame:
            parser.error('supply a log, --session and an inclusive valid frame range')
        with args.log.open(encoding='utf-8-sig') as lines:
            print(json.dumps(rank(lines, args.first_frame, args.last_frame, args.session), indent=2))
