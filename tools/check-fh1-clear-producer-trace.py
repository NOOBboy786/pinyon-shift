"""Exercise production clear observation: disabled, nesting, mismatch and limits."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default='clang++')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
source = (repo/'src/native_renderer/graphics_hooks.cpp').read_text()
state = source[source.index('using ClearClock ='):source.index('}  // namespace')]
hooks = source[source.index('void PinyonShiftObserveClearProducerBegin('):source.index('void PinyonShiftObserveSceneCommandBuffer(')]
config = tomllib.loads((repo/'config/rexglue/analysis/main-xex.toml').read_text())
expected = {0x8240E130: ('PinyonShiftObserveClearProducerBegin', ['r3','r4','r5','r6','r8','r1','f1']),
            0x8240E7A4: ('PinyonShiftObserveClearProducerEnd', ['r31','r1']),
            0x8240E4A8: ('PinyonShiftObserveClearShaderCopy', ['r3','r4','r5']),
            0x8240E4F4: ('PinyonShiftObserveClearShaderCopy', ['r3','r4','r5']),
            0x8240CF68: ('PinyonShiftObserveClearCommandRefill', [])}
actual = {h['address']: (h['name'], h.get('registers', [])) for h in config['midasm_hook'] if h['name'].startswith('PinyonShiftObserveClear')}
assert actual == expected
assert all('jump_address' not in h and not h.get('after_instruction') for h in config['midasm_hook'] if h['address'] in expected)
harness = r'''
#include <atomic>
#include <chrono>
#include <cassert>
#include <cstdint>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
union PPCRegister { uint64_t u64; uint32_t u32; double f64; };
bool trace_flag;
#define REXCVAR_GET(name) trace_flag
namespace rex::perf {
enum class CounterId { kSourceFrameCount };
int64_t GetTotalCounter(CounterId) { return 42; }
}
std::mutex log_mutex;
std::vector<std::vector<std::string>> records;
template<class T> std::string text(T value) { std::ostringstream o; o << value; return o.str(); }
template<class... T> void Log(const char* format, T... values) {
  std::lock_guard lock(log_mutex);
  records.push_back({format, text(values)...});
}
#define REXGPU_INFO(...) Log(__VA_ARGS__)
''' + state + hooks + r'''
int main(int argc, char**) {
  trace_flag = argc > 1;
  PPCRegister device{123}, flags{16}, rect{456}, colour{789}, stencil{2}, stack{4096}, depth{};
  depth.f64=1.0;
  auto begin = [&] { PinyonShiftObserveClearProducerBegin(device,flags,rect,colour,stencil,stack,depth); };
  auto end = [&] { PPCRegister inside{3840}; PinyonShiftObserveClearProducerEnd(device,inside); };
  PPCRegister destination{9000}, vertex{0x820C5FD0}, bytes{108};
  begin();
  PinyonShiftObserveClearShaderCopy(destination,vertex,bytes);
  PinyonShiftObserveClearCommandRefill();
  end();
  assert(device.u64==123 && flags.u64==16 && rect.u64==456 && stack.u64==4096 && depth.f64==1.0);
  assert(destination.u64==9000 && vertex.u64==0x820C5FD0 && bytes.u64==108);
  if (!trace_flag) { assert(clear_producers.empty() && records.empty() && clear_producer_records==0); return 0; }
  assert(clear_producers.empty() && records.size()==1);
  assert(records[0][3]=="42" && records[0][4]=="123" && records[0][5]=="16");
  assert(std::stoll(records[0][10])>=0 && records[0][11]=="1" && records[0][12]=="108");
  assert(records[0][13]==std::to_string(vertex.u32) && records[0][14]=="9000" && records[0][15]=="1" && records[0][16]=="0");
  begin();
  PinyonShiftObserveClearShaderCopy(destination,vertex,bytes);
  begin();
  bytes.u32=36;
  PinyonShiftObserveClearShaderCopy(destination,colour,bytes);
  end(); end();
  assert(records[1][12]=="36" && records[1][16]=="0");
  assert(records[2][12]=="108" && records[2][16]=="1");
  begin();
  std::thread other([] { assert(clear_producers.empty()); PinyonShiftObserveClearCommandRefill(); });
  other.join();
  end(); assert(records.back()[15]=="0");
  end(); assert(records.back()[0].find("unmatched end")!=std::string::npos);
  begin(); PPCRegister bad_stack{0}; PinyonShiftObserveClearProducerEnd(device,bad_stack);
  assert(clear_producers.empty() && records.back()[0].find("unmatched end")!=std::string::npos);
  begin(); PPCRegister bad_device{1}, inside{3840}; PinyonShiftObserveClearProducerEnd(bad_device,inside);
  assert(clear_producers.empty() && records.back()[0].find("unmatched end")!=std::string::npos);
  clear_producer_records=100000;
  begin(); end(); assert(records.back()[0].find("record limit reached")!=std::string::npos);
  auto count=records.size(); begin(); end(); assert(records.size()==count && clear_producers.empty());
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path/'check.cpp').write_text(harness)
    subprocess.run([args.compiler, '-std=c++20', str(path/'check.cpp'), '-o', str(path/'check.exe')], check=True)
    for argv in ([], ['enabled']):
        subprocess.run([str(path/'check.exe'), *argv], check=True)
print('clear trace disabled, non-mutation, pairing, nesting, thread isolation and cap checks passed')
