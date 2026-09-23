import importlib.util
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "extract-snr01-run-log.py"
spec = importlib.util.spec_from_file_location("snr01_filter", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExtractSnr01RunLogTest(unittest.TestCase):
    def test_excludes_previous_run_in_rotated_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            session = root / "20260923T052728Z-p30692.jsonl"
            session.touch()
            start = datetime(2026, 9, 23, 5, 27, 28, tzinfo=timezone.utc)
            end = start + timedelta(minutes=1, seconds=58)
            os.utime(session, (end.timestamp(), end.timestamp()))
            stamp = lambda time: time.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            old = stamp(start - timedelta(minutes=11))
            first = stamp(start)
            last = stamp(end)
            (root / "runtime.1.log").write_text(
                f"[{old}.000] FH1 SNR01 old\n"
                f"[{first}.000] FH1 SNR01 first\n"
            )
            (root / "runtime.log").write_text(
                f"[{last}.000] FH1 clear producer last\n"
            )
            output = root / "filtered.log"
            assert module.extract(session, output) == 2
            assert output.read_text() == (
                f"[{first}.000] FH1 SNR01 first\n"
                f"[{last}.000] FH1 clear producer last\n"
            )


if __name__ == "__main__":
    unittest.main()
