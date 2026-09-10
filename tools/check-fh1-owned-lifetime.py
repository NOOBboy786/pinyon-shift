"""Exercise production ownership lifetime and full-tile clear claims without a GPU."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default='clang++')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
source = (root / 'thirdparty/shiftglue-sdk/src/graphics/pipeline/render_target/cache.cpp').read_text()
header = (root / 'thirdparty/shiftglue-sdk/include/rex/graphics/pipeline/render_target/cache.h').read_text()
range_start = header.index('  struct OwnershipRange {')
ownership_range = header[range_start:header.index('\n  };', range_start) + 5]
methods = []
for signature in (
    'RenderTargetCache::RenderTarget* RenderTargetCache::GetFullyOwnedRenderTarget(',
    'void RenderTargetCache::ClearCache()',
    'void RenderTargetCache::DestroyAllRenderTargets(bool shutting_down)',
    'RenderTargetCache::RenderTarget* RenderTargetCache::PrepareFh1FullTileDepthClear(',
):
    start = source.index(signature)
    end = source.index('\n}', start) + 2
    methods.append(source[start:end])
start = source.index('void RenderTargetCache::ChangeOwnership(')
methods.append(source[start:source.index('\n}', start) + 2].replace(
    'RenderTargetCache::ChangeOwnership(', 'RenderTargetCache::ChangeOwnershipObserved(', 1))

# Minimal resource shell; method bodies above come directly from production.
code = r'''
#include <cassert>
#include <algorithm>
#include <array>
#include <cstdint>
#include <iterator>
#include <map>
#include <span>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#define assert_true(value, ...) assert(value)
#define assert_false(value) assert(!(value))
#define assert_not_null(value) assert(value)
namespace xenos {
constexpr uint32_t kEdramTileCount = 2048;
enum class MsaaSamples { k1X, k2X, k4X };
enum class DepthRenderTargetFormat { kD24S8, kD24FS8 };
}
struct RenderTargetKey {
  uint32_t value = 0;
  bool is_depth = true;
  uint32_t base_tiles = 0, pitch = 16;
  xenos::MsaaSamples msaa_samples = xenos::MsaaSamples::k4X;
  xenos::DepthRenderTargetFormat format = xenos::DepthRenderTargetFormat::kD24S8;
  uint32_t GetPitchTiles() const { return pitch; }
  bool Is64bpp() const { return false; }
  auto GetDepthFormat() const { return format; }
  bool IsEmpty() const { return !value; }
  bool operator==(const RenderTargetKey&) const = default;
  struct Hasher { size_t operator()(RenderTargetKey k) const { return k.value; } };
};
struct RenderTargetCache {
  enum class Path { kHostRenderTargets, kPixelShaderInterlock };
  Path path = Path::kHostRenderTargets;
  Path GetPath() const { return path; }
  bool different = false, fail_creation = false, accumulated_valid = true;
  bool IsHostDepthEncodingDifferent(xenos::DepthRenderTargetFormat) const { return different; }
  void ResetAccumulatedRenderTargets() { accumulated_valid = false; }
  inline static int destroyed = 0;
  struct RenderTarget {
    RenderTargetKey identity;
    int generation;
    RenderTargetKey key() const { return identity; }
    ~RenderTarget() { ++destroyed; }
  };
  OWNERSHIP_RANGE
  struct Transfer {
    struct Rectangle {};
    uint32_t start_tiles, end_tiles;
    RenderTarget* source;
    RenderTarget* host_depth_source;
    Transfer(uint32_t start, uint32_t end, RenderTarget* src, RenderTarget* history)
        : start_tiles(start), end_tiles(end), source(src), host_depth_source(history) {}
    template<class... Args> static uint32_t GetRangeRectangles(Args...) {
      assert(false); return 0; // Full-tile claims must never request imports.
    }
  };
  std::map<uint32_t, OwnershipRange> ownership_ranges_;
  std::unordered_map<RenderTargetKey, RenderTarget*, RenderTargetKey::Hasher> render_targets_;
  RenderTarget* GetFullyOwnedRenderTarget(RenderTargetKey key) const;
  void ClearCache();
  void DestroyAllRenderTargets(bool shutting_down);
  RenderTarget* PrepareFh1FullTileDepthClear(RenderTargetKey, std::span<const std::array<uint32_t, 4>>);
  RenderTarget* GetOrCreateRenderTarget(RenderTargetKey key) {
    if (fail_creation) return nullptr;
    auto& p = render_targets_[key];
    if (!p) p = new RenderTarget{key, 1};
    return p;
  }
  std::vector<std::array<uint32_t,2>> claims;
  void ChangeOwnershipObserved(RenderTargetKey, uint32_t, uint32_t,
      std::vector<Transfer>*, const Transfer::Rectangle* = nullptr);
  void ChangeOwnership(RenderTargetKey key, uint32_t start, uint32_t length, void* transfers) {
    // Record calls, then execute the production ownership implementation.
    assert(!transfers && render_targets_.contains(key));
    claims.push_back({start,length});
    ChangeOwnershipObserved(key,start,length,nullptr);
  }
};
METHODS
int main() {
  RenderTargetCache c;
  RenderTargetKey owner{1}, unorm{2}, floating{3}, orphan{4};
  assert(!c.GetFullyOwnedRenderTarget(owner));
  c.ownership_ranges_.emplace(0, RenderTargetCache::OwnershipRange{2048, owner, unorm, floating});
  assert(!c.GetFullyOwnedRenderTarget(owner));
  c.render_targets_[owner] = nullptr;
  assert(!c.GetFullyOwnedRenderTarget(owner));
  for (auto key : {owner, unorm, floating, orphan})
    c.render_targets_[key] = new RenderTargetCache::RenderTarget{key, 1};
  auto* original = c.GetFullyOwnedRenderTarget(owner);
  assert(original && !c.GetFullyOwnedRenderTarget({}));
  c.ClearCache();
  assert(c.render_targets_.size() == 3 && c.destroyed == 1);
  assert(c.GetFullyOwnedRenderTarget(owner) == original);
  assert(c.render_targets_.contains(unorm) && c.render_targets_.contains(floating));
  c.ownership_ranges_.begin()->second.end_tiles = 1000;
  c.ownership_ranges_.emplace(1000, RenderTargetCache::OwnershipRange{2048, unorm, {}, {}});
  assert(!c.GetFullyOwnedRenderTarget(owner));
  c.ownership_ranges_.at(1000).render_target = owner;
  assert(c.GetFullyOwnedRenderTarget(owner) == original);
  c.DestroyAllRenderTargets(false);
  assert(c.destroyed == 4 && c.render_targets_.empty());
  assert(c.ownership_ranges_.size() == 1 && !c.GetFullyOwnedRenderTarget(owner));
  c.render_targets_[owner] = new RenderTargetCache::RenderTarget{owner, 2};
  assert(!c.GetFullyOwnedRenderTarget(owner));
  c.ownership_ranges_.begin()->second.render_target = owner;
  assert(c.GetFullyOwnedRenderTarget(owner)->generation == 2);
  c.DestroyAllRenderTargets(true);
  assert(c.destroyed == 5 && c.ownership_ranges_.empty() && c.render_targets_.empty());
  assert(!c.GetFullyOwnedRenderTarget(owner));
  RenderTargetCache t;
  // The captured first clear starts with mixed color/depth owners and distinct
  // independent histories. Check all 2048 tiles against a separate flat model.
  uint32_t start=0;
  for (uint32_t end : {192u,720u,1440u,2048u}) {
    t.ownership_ranges_.emplace(start,RenderTargetCache::OwnershipRange{
        end,RenderTargetKey{10+start},RenderTargetKey{30+start},RenderTargetKey{40+start}});
    start=end;
  }
  const auto tile_owners = [&]() {
    std::array<std::array<RenderTargetKey,3>,2048> result;
    uint32_t previous_end=0;
    for (const auto& [first,r] : t.ownership_ranges_) {
      assert(first==previous_end && r.end_tiles>first && r.end_tiles<=2048);
      for (uint32_t tile=first;tile<r.end_tiles;++tile)
        result[tile]={r.render_target,r.host_depth_render_target_unorm24,r.host_depth_render_target_float24};
      previous_end=r.end_tiles;
    }
    assert(previous_end==2048);
    return result;
  };
  const auto initial=tile_owners();
  const std::array<std::array<uint32_t,4>,2> rows{{{0,0,2,6},{3,11,4,47}}};
  const auto reject = [&](auto key, auto rectangles) {
    t.accumulated_valid = true;
    const auto old_claims=t.claims.size(), old_targets=t.render_targets_.size();
    assert(!t.PrepareFh1FullTileDepthClear(key,rectangles));
    assert(t.claims.size()==old_claims && t.render_targets_.size()==old_targets && t.accumulated_valid);
    assert(tile_owners()==initial);
  };
  auto bad_rows=rows; bad_rows[1][2]=17;
  reject(owner,std::span(bad_rows)); // Reject all rectangles before claiming any.
  bad_rows=rows; bad_rows[1][3]=UINT32_MAX; reject(owner,std::span(bad_rows));
  bad_rows=rows; bad_rows[1][3]=bad_rows[1][1]; reject(owner,std::span(bad_rows));
  reject(owner,std::span<const std::array<uint32_t,4>>{});
  auto bad_key=owner; bad_key.base_tiles=1; reject(bad_key,std::span(rows));
  bad_key=owner; bad_key.pitch=0; reject(bad_key,std::span(rows));
  bad_key=owner; bad_key.is_depth=false; reject(bad_key,std::span(rows));
  bad_key=owner; bad_key.msaa_samples=xenos::MsaaSamples::k1X; reject(bad_key,std::span(rows));
  bad_key=owner; bad_key.format=xenos::DepthRenderTargetFormat::kD24FS8; reject(bad_key,std::span(rows));
  t.different=true; reject(owner,std::span(rows)); t.different=false;
  t.path=RenderTargetCache::Path::kPixelShaderInterlock; reject(owner,std::span(rows));
  t.path=RenderTargetCache::Path::kHostRenderTargets;
  t.fail_creation=true; reject(owner,std::span(rows)); t.fail_creation=false;
  assert(t.PrepareFh1FullTileDepthClear(owner,rows) && !t.accumulated_valid);
  assert(t.claims.size()==42);
  for (uint32_t i=0; i<42; ++i) {
    const uint32_t y=i<6?i:i+5;
    const std::array<uint32_t,2> expected{16*y+(i<6?0u:3u),i<6?2u:1u};
    assert(t.claims[i]==expected);
  }
  const auto actual=tile_owners();
  for (uint32_t tile=0;tile<2048;++tile) {
    const auto x=tile%16,y=tile/16;
    const bool written=(y<6 && x<2) || (y>=11 && y<47 && x==3);
    assert(actual[tile][0]==(written?owner:initial[tile][0]));
    assert(actual[tile][1]==initial[tile][1] && actual[tile][2]==initial[tile][2]);
  }
  auto* tile_target = t.render_targets_.at(owner);
  for (const auto& owners : actual)
    for (auto key : owners)
      if (!key.IsEmpty() && !t.render_targets_.contains(key))
        t.render_targets_[key] = new RenderTargetCache::RenderTarget{key, 1};
  t.render_targets_[orphan] = new RenderTargetCache::RenderTarget{orphan, 1};
  t.ClearCache();
  assert(!t.render_targets_.contains(orphan));
  assert(t.render_targets_.at(owner) == tile_target && tile_owners() == actual);
  for (const auto& owners : actual)
    for (auto key : owners) assert(t.render_targets_.contains(key));
  t.DestroyAllRenderTargets(false);
  assert(t.render_targets_.empty());
  const auto reset_owners = tile_owners();
  for (const auto& owners : reset_owners)
    for (auto key : owners) assert(key.IsEmpty());
  t.claims.clear();
  assert(t.PrepareFh1FullTileDepthClear(owner, rows));
  assert(t.render_targets_.size() == 1 && t.claims.size() == 42);
  const auto recreated = tile_owners();
  for (uint32_t tile=0; tile<2048; ++tile) {
    assert(recreated[tile][0] == (actual[tile][0] == owner ? owner : RenderTargetKey{}));
    assert(recreated[tile][1].IsEmpty() && recreated[tile][2].IsEmpty());
  }
  t.DestroyAllRenderTargets(true);
}
'''.replace('OWNERSHIP_RANGE', ownership_range).replace('METHODS', '\n'.join(methods))
with tempfile.TemporaryDirectory(prefix='fh1-owned-lifetime-') as directory:
    cpp = Path(directory) / 'check.cpp'
    exe = Path(directory) / 'check.exe'
    cpp.write_text(code)
    subprocess.run([args.compiler, '-std=c++20', '-O2', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('PASS: production ownership lifetime and atomic full-tile clear row admission')
