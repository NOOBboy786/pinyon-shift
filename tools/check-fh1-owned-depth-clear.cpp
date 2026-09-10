#include <rex/graphics/d3d12/fh1_clear.h>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <optional>
using Rect = std::array<uint32_t, 4>;
// Candidate mapping only: same D24S8 base and pitch, 4 samples to 1 sample.
// The ownership gate must independently prove every touched tile is owned.
std::optional<Rect> map_clear(Rect r, uint32_t scale, uint32_t pitch) {
  rex::graphics::d3d12::Fh1ClearRectangle input{{int32_t(r[0]),int32_t(r[1]),int32_t(r[2]),int32_t(r[3])},0.5f};
  auto mapped=rex::graphics::d3d12::fh1_clear_to_single_sample(input,scale,pitch);
  if (!mapped) return {};
  return Rect{uint32_t(mapped->bounds[0]),uint32_t(mapped->bounds[1]),uint32_t(mapped->bounds[2]),uint32_t(mapped->bounds[3])};
}
// Independent tile decomposition follows CreateTransferPixelShader's
// destination tile division, sample-bit insertion, wrap and source division.
std::array<uint32_t,2> reference(uint32_t x,uint32_t y,uint32_t sample,
                                uint32_t scale,uint32_t pitch) {
  uint32_t tw=40*scale, th=8*scale;
  uint32_t tile=((y/th)*pitch+x/tw)&2047;
  return {80*scale*(tile%pitch)+2*(x%tw)+(sample&1),
          16*scale*(tile/pitch)+2*(y%th)+(sample>>1)};
}
bool inside(Rect r,uint32_t x,uint32_t y) {
  return x>=r[0] && x<r[2] && y>=r[1] && y<r[3];
}
int main() {
  using rex::graphics::d3d12::fh1_clear_to_single_sample;
  using rex::graphics::d3d12::Fh1ClearRectangle;
  assert(!fh1_clear_to_single_sample({{-1,0,1,1},0.5f},1,13));
  assert(!fh1_clear_to_single_sample({{0,0,1,1},-0.1f},1,13));
  assert(!fh1_clear_to_single_sample({{0,0,1,1},1.1f},1,13));
  assert(!fh1_clear_to_single_sample({{0,0,1,1},std::numeric_limits<float>::quiet_NaN()},1,13));
  assert(!fh1_clear_to_single_sample({{0,0,1,1},std::numeric_limits<float>::infinity()},1,13));
  assert(fh1_clear_to_single_sample({{0,0,1,1},0.25f},1,13)->depth == 0.25f);
  uint64_t samples=0;
  for(uint32_t scale: {1u,2u}) {
    using rex::graphics::d3d12::fh1_zero_clear_tiles;
    for (Rect base : {Rect{0,0,80,48}, Rect{0,0,40,32}, Rect{40,8,120,24}}) {
      Fh1ClearRectangle r{{int32_t(base[0]*scale),int32_t(base[1]*scale),
                           int32_t(base[2]*scale),int32_t(base[3]*scale)},0};
      const Rect expected{base[0]/40,base[1]/8,base[2]/40,base[3]/8};
      assert(fh1_zero_clear_tiles(r,scale,16)==expected);
      // Every sample of every admitted tile is overwritten; a partial edge
      // would discard old contents and must reject rather than round outwards.
      for (uint32_t edge=0; edge<4; ++edge) {
        auto partial=r; ++partial.bounds[edge];
        assert(!fh1_zero_clear_tiles(partial,scale,16));
      }
      r.depth=1; assert(!fh1_zero_clear_tiles(r,scale,16));
    }
    assert(!fh1_zero_clear_tiles({{0,0,0,8},0},scale,16));
    assert(!fh1_zero_clear_tiles({{0,0,40,8},0},3,16));
    // Capture rectangles at 2x, reduced to corresponding 1x boundaries.
    for(Rect original: {Rect{560,512,960,1024},Rect{0,0,960,1024},
                        Rect{0,0,480,512},Rect{1,1,81,17}}) {
      Rect r=original;
      if(scale==1) for(auto& v:r) v/=2;
      auto mapped=map_clear(r,scale,13);
      assert(mapped);
      // Include a one-pixel guard on every side to verify partial-write bounds.
      for(uint32_t y=r[1]?r[1]-1:0;y<=r[3];++y)
        for(uint32_t x=r[0]?r[0]-1:0;x<=r[2];++x)
          for(uint32_t s=0;s<4;++s) {
            auto xy=reference(x,y,s,scale,13);
            assert(inside(r,x,y)==inside(*mapped,xy[0],xy[1]));
            assert(xy[0]==2*x+(s&1) && xy[1]==2*y+(s>>1));
            ++samples;
          }
    }
    const uint32_t tw=40*scale,th=8*scale;
    assert(map_clear({0,0,13*tw,157*th},scale,13));
    assert(map_clear({0,157*th,7*tw,158*th},scale,13));
    assert(!map_clear({0,157*th,7*tw+1,158*th},scale,13));
    assert(!map_clear({0,0,13*tw+1,th},scale,13));
    assert(!map_clear({0,158*th,tw,159*th},scale,13));
  }
  assert(!map_clear({0,0,1,1},0,13));
  assert(!map_clear({0,0,1,1},1,0));
  assert(!map_clear({1,1,1,2},1,13));
  std::printf("PASS: %llu sample mappings, partial-region guards and wrap rejection\n",
              static_cast<unsigned long long>(samples));
}
