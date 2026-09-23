"""Queue the three SNR-04 frames from qrenderdoc --python while the game runs."""

import json
import os
from pathlib import Path
import sys
import time
import traceback

import renderdoc as rd

out = Path(os.environ['SNR04_OUTPUT'])
state = {'stage': 'waiting_target', 'captures': []}


def save():
    out.write_text(json.dumps(state))


start = time.monotonic()
target = None
try:
    save()
    while time.monotonic() - start < 60 and target is None:
        previous = 0
        for _ in range(20):
            ident = rd.EnumerateRemoteTargets('localhost', previous)
            if not ident or ident <= previous:
                break
            previous = ident
            candidate = rd.CreateTargetControl('localhost', ident, 'snr04 capture', True)
            if candidate and 'pinyon_shift' in str(candidate.GetTarget()).lower():
                target = candidate
                state['pid'] = target.GetPID()
                break
            if candidate:
                candidate.Shutdown()
        if target is None:
            time.sleep(.25)
    if target is None:
        raise RuntimeError('game target not found')
    state['stage'] = 'waiting_api'
    save()
    while time.monotonic() - start < 90 and not target.GetAPI():
        target.ReceiveMessage(None)
        time.sleep(.05)
    if str(target.GetAPI()) != 'D3D12':
        raise RuntimeError('D3D12 target did not register')
    target.QueueCapture(6000, 3)
    state['stage'] = 'queued'
    save()
    while time.monotonic() - start < 300 and target.Connected() and len(state['captures']) < 3:
        message = target.ReceiveMessage(None)
        if message.type == rd.TargetControlMessageType.NewCapture:
            state['captures'].append(str(message.newCapture.path))
            save()
        time.sleep(.05)
    state['stage'] = 'done' if len(state['captures']) == 3 else 'incomplete'
    save()
except Exception:
    state.update(stage='error', error=traceback.format_exc())
    save()
finally:
    if target:
        target.Shutdown()
sys.exit(0)
