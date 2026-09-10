// Standalone contract check; captured inputs are supplied locally, never
// embedded.
#define XXH_INLINE_ALL
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <rex/graphics/fh1_mip_contract.h>
#include <string>
#include <vector>

using namespace rex::graphics;
std::vector<uint8_t> Read(const std::filesystem::path &path) {
  std::ifstream file(path, std::ios::binary);
  assert(file);
  return {std::istreambuf_iterator<char>(file),
          std::istreambuf_iterator<char>()};
}

int main(int argc, char **argv) {
  assert(argc == 2 || argc == 3);
  assert(Fh1MipInheritedState(0, 0x20002000, 0, 0xFFFFFF, 0xFF000, 0xFF100));
  assert(!Fh1MipInheritedState(1, 0x20002000, 0, 0xFFFFFF, 0xFF000, 0xFF100));
  assert(!Fh1MipInheritedState(0, 0x007F0080, 0, 0xFFFFFF, 0xFF000, 0xFF100));
  assert(!Fh1MipInheritedState(0, 0x20002000, 1, 0xFFFFFF, 0xFF000, 0xFF100));
  assert(!Fh1MipInheritedState(0, 0x20002000, 0, 22, 0xFF000, 0xFF100));
  assert(!Fh1MipInheritedState(0, 0x20002000, 0, 0xFFFFFF, 0xFF001, 0xFF100));
  const std::filesystem::path root(argv[1]);
  std::map<uint32_t, std::vector<uint8_t>> memory;
  for (const auto &entry :
       std::filesystem::directory_iterator(root / "memory")) {
    memory.emplace(
        uint32_t(std::stoul(entry.path().stem().string(), nullptr, 16)),
        Read(entry.path()));
  }
  auto copy = [&](uint32_t address, std::span<uint8_t> bytes) {
    auto it = memory.find(address);
    if (it == memory.end() || it->second.size() != bytes.size())
      return false;
    std::memcpy(bytes.data(), it->second.data(), bytes.size());
    return true;
  };
  for (uint32_t face = 0; face < 6; ++face) {
    auto commands = Read(root / ("face-" + std::to_string(face) + ".bin"));
    Fh1MipChain chain;
    XXH128_hash_t signature{};
    const bool admitted = ParseFh1MipChain(commands, chain, &signature);
    if (argc == 3 && std::string(argv[2]) == "--signature") {
      std::cout << std::hex << signature.low64 << ' ' << signature.high64
                << '\n';
      continue;
    }
    assert(admitted && chain.face == face && chain.base == 0x1C879000);
    assert(CheckFh1MipInputs(chain, copy));
    assert(!CheckFh1MipInputs(
        chain, [](uint32_t, std::span<uint8_t>) { return false; }));
    for (auto &[address, bytes] : memory) {
      bytes.front() ^= 0x80;
      assert(!CheckFh1MipInputs(chain, copy));
      bytes.front() ^= 0x80;
    }
    auto bad = commands;
    bad[492] ^= 1; // Change a draw packet, not its allocation address.
    assert(!ParseFh1MipChain(bad, chain));
    bad = commands;
    Fh1MipWriteWord(bad.data() + 512, 0x1FFFFFFF); // Invalid mip destination.
    assert(!ParseFh1MipChain(bad, chain));
    assert(!ParseFh1MipChain(std::span(commands).first(commands.size() - 4),
                             chain));

    // Relocate the cube and every external allocation, preserving their bytes.
    constexpr uint32_t delta = 0x100000;
    auto relocated = commands;
    uint32_t vf0 = 0;
    for (uint32_t i = 0; i < relocated.size() / 4;) {
      const uint32_t header = Fh1MipReadWord(relocated.data() + i++ * 4);
      const uint32_t type = header >> 30;
      const uint32_t size = type == 2 ? 0 : ((header >> 16) & 0x3FFF) + 1;
      for (uint32_t j = 0; j < size; ++j) {
        auto *p = relocated.data() + (i + j) * 4;
        const uint32_t value = Fh1MipReadWord(p);
        if (type == 0) {
          const uint32_t reg = (header & 0x7FFF) + ((header & 0x8000) ? 0 : j);
          if (reg == 0x4800)
            vf0 = value;
          if (reg == 0x2319 || (reg == 0x4801 && (vf0 & 3) != 3) ||
              ((reg == 0x4800 || reg == 0x48BE) && (value & 3) == 3)) {
            Fh1MipWriteWord(p, value + delta);
          }
        } else if (type == 3 && j == 0 &&
                   (((header >> 8) & 0x7F) == 0x27 ||
                    ((header >> 8) & 0x7F) == 0x2F)) {
          Fh1MipWriteWord(p, value + delta);
        }
      }
      i += size;
    }
    assert(ParseFh1MipChain(relocated, chain) && chain.face == face &&
           chain.base == 0x1C879000 + delta);
    assert(CheckFh1MipInputs(
        chain, [&](uint32_t address, std::span<uint8_t> bytes) {
          return address >= delta && copy(address - delta, bytes);
        }));
  }
  if (argc == 2)
    std::cout << "six faces, relocation, external mutations, ownership "
                 "rejection and malformed inputs pass\n";
}
