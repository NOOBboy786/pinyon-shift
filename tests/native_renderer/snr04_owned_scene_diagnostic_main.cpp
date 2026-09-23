#include <exception>
#include <iostream>

#include "native_renderer/snr04_owned_scene_diagnostic.h"

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: snr04-owned-scene-diagnostic FIXTURE VS_DXBC OUTPUT_DIR\n";
    return 1;
  }
  try {
    const auto covered = pinyon_shift::native_renderer::RunSnr04OwnedSceneDiagnostic(
        argv[1], argv[2], argv[3]);
    std::cout << "SNR04 diagnostic covered_pixels=" << covered << '\n';
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
