"""Exercise the production CSV writer's Windows read-sharing and size stop."""
from pathlib import Path
import subprocess
import tempfile
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default='clang++')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
source = (repo / 'thirdparty/shiftglue-sdk/src/core/perf/counter.cpp').read_text()
functions = source[source.index('void SetCsvLogPath('):source.index('\n}  // namespace rex::perf')]
processor = (repo / 'thirdparty/shiftglue-sdk/src/graphics/d3d12/command_processor.cpp').read_text()
start = processor.index('static bool Fh1ObserveCorpusFrame(')
sampling = processor[start:processor.index('\n}', start) + 2]
assert 'if (!Fh1ObserveCorpusFrame(observation_frame_sequence_)) {\n    prepared_draw_observer = nullptr;' in processor
assert 'if (!Fh1ObserveCorpusFrame(observation_frame_sequence_)) {\n    copy_observer = nullptr;' in processor
harness = r'''
#include <array>
#include <atomic>
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <filesystem>
#include <string>
#include <share.h>
#define REX_PLATFORM_WIN32 1
#define REXLOG_WARN(...) ((void)0)
#define REXCVAR_GET(name) ::limit_mb
namespace rex {
auto to_path(const std::string& path) { return std::filesystem::path(path); }
namespace filesystem { auto Tell(FILE* file) { return _ftelli64(file); } }
}
constexpr size_t kNumCounters = 1;
const char* kCounterNames[] = {"frame_time_us"};
std::array<std::atomic<int64_t>, 1> g_snapshot{};
FILE* g_csv_file = nullptr;
std::string g_csv_path;
uint64_t g_csv_frame_count = 0;
int limit_mb = 0;
void FlushCsv();
''' + functions + sampling + r'''
int main() {
  for (uint64_t frame = 0; frame < 181; ++frame) {
    limit_mb = 0;
    assert(Fh1ObserveCorpusFrame(frame));
    limit_mb = 1;
    assert(Fh1ObserveCorpusFrame(frame) == (frame % 60 == 0));
  }
  SetCsvLogPath("record.csv");
  assert(g_csv_file);
  auto* reader = _fsopen("record.csv", "r", _SH_DENYNO);
  assert(reader);  // A live recorder can read while the game owns the writer.
  fclose(reader);
  limit_mb = 1;
  assert(_fseeki64(g_csv_file, 1024 * 1024, SEEK_SET) == 0);
  g_csv_frame_count = 59;
  WriteCsvFrame();
  assert(!g_csv_file);
  WriteCsvFrame();  // Capped recording is harmless to continued gameplay.
  limit_mb = 0;
  SetCsvLogPath("unlimited.csv");
  assert(_fseeki64(g_csv_file, 1024 * 1024, SEEK_SET) == 0);
  g_csv_frame_count = 59;
  WriteCsvFrame();
  assert(g_csv_file);
  FlushCsv();
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / 'check.cpp').write_text(harness)
    subprocess.run([args.compiler, '-std=c++20', str(path/'check.cpp'), '-o', str(path/'check.exe')], check=True)
    subprocess.run([str(path/'check.exe')], cwd=path, check=True)
print('discovery CSV sharing / cap checks passed')
