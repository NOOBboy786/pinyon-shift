#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <Windows.h>

#include <rex/graphics/d3d12/fh1_shader_pack.h>

int main(int argc, char** argv) {
  assert(argc == 2);
  using rex::graphics::d3d12::Fh1ShaderPack;
  const Fh1ShaderPack::Config config{0x20260827, 0x10DE, 0xD, 1, 1};
  Fh1ShaderPack pack;
  std::string error;
  assert(pack.Load(std::filesystem::path(argv[1]), config, &error));
  assert(pack.size() == 1);
  const auto* entry = pack.Find(rex::graphics::xenos::ShaderType::kPixel, 1, 2);
  assert(entry);
  assert(entry->bytecode.size() == 9);
  assert(std::memcmp(entry->bytecode.data(), "DXBCpixel", 9) == 0);
  MEMORY_BASIC_INFORMATION mapping_info{};
  assert(VirtualQuery(entry->bytecode.data(), &mapping_info, sizeof(mapping_info)));
  assert(mapping_info.Type == MEM_MAPPED);
  assert(mapping_info.Protect == PAGE_READONLY);
  assert(entry->texture_bindings.size() == 1);
  assert(entry->texture_bindings[0].fetch_constant == 3);
  assert(entry->sampler_bindings.size() == 1);
  assert(entry->used_texture_mask == (1u << 3));

  Fh1ShaderPack::Config incompatible = config;
  incompatible.draw_resolution_scale_x = 2;
  assert(!pack.Load(std::filesystem::path(argv[1]), incompatible, &error));
  assert(error == "incompatible_header");
  assert(pack.size() == 0);
  assert(!pack.Find(rex::graphics::xenos::ShaderType::kPixel, 1, 2));
  assert(pack.Load(std::filesystem::path(argv[1]), config, &error));
  pack.Clear();
  assert(pack.size() == 0);
  // Clearing must release the read-only mapping and its write-denying handle.
  HANDLE writable = CreateFileW(std::filesystem::path(argv[1]).c_str(), GENERIC_WRITE,
                                 FILE_SHARE_READ, nullptr, OPEN_EXISTING, 0, nullptr);
  assert(writable != INVALID_HANDLE_VALUE);
  CloseHandle(writable);

  const auto damaged = std::filesystem::path(argv[1]).concat(".damaged");
  std::filesystem::copy_file(argv[1], damaged, std::filesystem::copy_options::overwrite_existing);
  {
    std::fstream file(damaged, std::ios::binary | std::ios::in | std::ios::out);
    file.seekp(-1, std::ios::end);
    file.put('\xFF');
  }
  assert(!pack.Load(damaged, config, &error));
  assert(error == "content_hash_mismatch");
  assert(pack.size() == 0);
  std::filesystem::remove(damaged);
  return 0;
}
