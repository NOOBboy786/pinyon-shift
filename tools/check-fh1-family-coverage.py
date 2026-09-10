"""Exercise production family/pass recording and inventory limits."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default='clang++')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
source = (repo/'src/native_renderer/fh1_gpu_corpus.cpp').read_text()
block = source[source.index('constexpr size_t kMaximumCorpusKeys'):source.index('}  // namespace')]
summary_source = (repo/'src/native_renderer/fh1_pass_tracker.h').read_text()
summary = summary_source[summary_source.index('struct Fh1PassSummary {'):summary_source.index('class Fh1PassTracker')]
reset = source[source.index('bool ResetFh1GpuCorpus()'):source.index('void RecordFh1GpuExecution(')]
assert 'g_shader_families.clear();' in reset and 'g_shader_family_overflow = 0;' in reset
harness = r'''
#include <atomic>
#include <array>
#include <cstdint>
#include <map>
#include <mutex>
#include <utility>
#include <cassert>
namespace rex::system {
enum class GraphicsFh1ExecutionKind { kDraw, kCopyResolve };
struct GraphicsFh1ExecutionKey {
  uint64_t identity;
  GraphicsFh1ExecutionKind kind = GraphicsFh1ExecutionKind::kDraw;
  bool operator==(const GraphicsFh1ExecutionKey&) const = default;
};
struct GraphicsCopyObservation {};
}
''' + summary + r'''
struct Fh1PassTracker {};
''' + block + r'''
int main() {
  using namespace rex::system;
  for (uint64_t id=1; id<=kMaximumCorpusKeys; ++id)
    assert(RecordKeyLocked(GraphicsFh1ExecutionKey{id}, id, 1, 2));
  assert(g_shader_families.size()==1);
  assert(!RecordKeyLocked(GraphicsFh1ExecutionKey{kMaximumCorpusKeys+1}, 70000, 3, 4));
  assert(g_overflow==1 && g_shader_families.at({3,4}).count==1);
  assert(!RecordKeyLocked(GraphicsFh1ExecutionKey{kMaximumCorpusKeys+2}, 70001, 3, 4));
  assert(g_shader_families.at({3,4}).count==2);
  assert(g_shader_families.at({3,4}).first_frame==70000);
  assert(g_shader_families.at({3,4}).last_frame==70001);
  RecordKeyLocked(GraphicsFh1ExecutionKey{90000, GraphicsFh1ExecutionKind::kCopyResolve}, 70002, 9, 9);
  assert(g_shader_families.size()==2);
  for (uint64_t n=2; n<kMaximumShaderFamilies; ++n)
    RecordKeyLocked(GraphicsFh1ExecutionKey{100000+n}, 70003, n+10, 0);
  assert(g_shader_families.size()==kMaximumShaderFamilies);
  RecordKeyLocked(GraphicsFh1ExecutionKey{200000}, 70004, 99999, 0);
  assert(g_shader_family_overflow==1);
  RecordKeyLocked(GraphicsFh1ExecutionKey{200001}, 70005, 3, 4);
  assert(g_shader_families.at({3,4}).count==3);
  assert(g_shader_family_overflow==1 && g_entries.size()==kMaximumCorpusKeys);
  Fh1PassSummary a{};
  a.signature=1; a.frame=60; a.attachment_state=2; a.first_draw_family=3;
  a.first_draw_identity=4; a.terminal_copy_state=5; a.draw_count=2;
  a.prepare_cpu_time_ns=100;
  RecordPassLocked(a);
  auto b=a; b.frame=120; b.first_draw_identity=6; b.prepare_cpu_time_ns=200;
  RecordPassLocked(b);
  const auto& pass=g_passes.at(1);
  assert(pass.occurrences==2 && pass.draw_executions==4 && !g_pass_collisions);
  assert(pass.first_frame==60 && pass.last_frame==120);
  assert(pass.summary.prepare_cpu_time_ns==300);
  assert(pass.first_draw_identity_varies && pass.summary.first_draw_identity==4);
  // Actual signature conflicts still reject and must not change totals.
  for (auto field : {&Fh1PassSummary::attachment_state,
                     &Fh1PassSummary::first_draw_family,
                     &Fh1PassSummary::terminal_copy_state}) {
    auto bad=a; ++(bad.*field); RecordPassLocked(bad);
  }
  auto bad=a; ++bad.draw_count; RecordPassLocked(bad);
  assert(g_pass_collisions==4 && pass.occurrences==2);
  for (uint64_t id=2; id<=kMaximumCorpusKeys; ++id) {
    auto next=a; next.signature=id; RecordPassLocked(next);
  }
  const auto overflow=g_overflow;
  auto next=a; next.signature=kMaximumCorpusKeys+1; RecordPassLocked(next);
  assert(g_overflow==overflow+1 && g_passes.size()==kMaximumCorpusKeys);
  RecordPassLocked(b);
  assert(g_overflow==overflow+1 && g_passes.at(1).occurrences==3);
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path/'check.cpp').write_text(harness)
    subprocess.run([args.compiler, '-std=c++20', str(path/'check.cpp'), '-o', str(path/'check.exe')], check=True)
    subprocess.run([str(path/'check.exe')], check=True)
print('family/pass coverage, identity variation, collision and saturation checks passed')
