// Diagnostic only: replay the SNR-03 owned fixture into private D3D12 targets.
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>
#include <d3d12.h>
#include <d3dcompiler.h>
#include <dxgi1_6.h>
#include <wrl/client.h>

#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <source_location>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "native_renderer/snr04_owned_scene_diagnostic.h"

using Microsoft::WRL::ComPtr;

namespace {
constexpr uint32_t width = 1280, height = 720;
constexpr char expected_vs_sha[] =
    "2adfe080228c468ce9aec7e21d19798fc8aaa32cdba5d7325c4fac4070f21faa";

void check(HRESULT result,
           std::source_location location = std::source_location::current()) {
  if (FAILED(result))
    throw std::runtime_error("D3D12 error " + std::to_string(uint32_t(result)) +
                             " at line " + std::to_string(location.line()));
}
void require(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}
std::vector<char> read(const std::filesystem::path& path) {
  std::ifstream file(path, std::ios::binary);
  require(bool(file), "missing input");
  return {std::istreambuf_iterator<char>(file), {}};
}
std::string sha256(const std::vector<char>& data) {
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  require(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0,
          "SHA-256 provider unavailable");
  std::array<UCHAR, 32> digest{};
  auto status = BCryptHash(algorithm, nullptr, 0,
                           reinterpret_cast<PUCHAR>(const_cast<char*>(data.data())),
                           ULONG(data.size()), digest.data(), ULONG(digest.size()));
  BCryptCloseAlgorithmProvider(algorithm, 0);
  require(status >= 0, "SHA-256 failed");
  std::ostringstream hex;
  for (auto byte : digest) hex << std::hex << std::setfill('0') << std::setw(2) << int(byte);
  return hex.str();
}

struct Reader {
  const std::vector<char>& data;
  size_t position = 0;
  template <typename T> T take() {
    require(position <= data.size() && sizeof(T) <= data.size() - position,
            "truncated fixture");
    T result;
    std::memcpy(&result, data.data() + position, sizeof(T));
    position += sizeof(T);
    return result;
  }
  std::vector<char> bytes(size_t count) {
    require(position <= data.size() && count <= data.size() - position,
            "truncated vertex bytes");
    std::vector<char> result(data.data() + position, data.data() + position + count);
    position += count;
    return result;
  }
};
struct Item {
  uint32_t packet = 0;
  uint32_t vertex_count = 0;
  std::array<uint32_t, 96> constants{};
  std::array<uint32_t, 40> system{};
  std::array<uint32_t, 40> original_system{};
  std::array<uint32_t, 4> fetch{};
  std::vector<char> vertices;
};
struct Scene {
  uint64_t source_frame = 0;
  std::string fixture_sha256;
  std::vector<Item> items;
};
Scene load_scene(const std::filesystem::path& path) {
  auto file = read(path);
  Reader reader{file};
  require(reader.take<std::array<char, 8>>() ==
              std::array<char, 8>{'S', 'N', 'R', '0', '3', 'F', '1', '\0'},
          "wrong fixture magic");
  Scene scene;
  scene.fixture_sha256 = sha256(file);
  scene.source_frame = reader.take<uint64_t>();
  reader.take<uint32_t>();  // Title view.
  reader.take<uint32_t>();  // Title camera.
  const auto count = reader.take<uint32_t>();
  require(count > 0 && count <= 512, "invalid item count");
  reader.take<std::array<uint32_t, 32>>();  // Two title camera word arrays.
  scene.items.reserve(count);
  std::set<uint32_t> packets;
  for (uint32_t ordinal = 0; ordinal < count; ++ordinal) {
    auto metadata = reader.take<std::array<uint32_t, 5>>();
    Item item;
    item.packet = reader.take<uint32_t>();
    require(packets.insert(item.packet).second, "duplicate packet");
    reader.take<uint64_t>();  // Bucket entry.
    item.vertex_count = reader.take<uint32_t>();
    const auto byte_count = reader.take<uint32_t>();
    const auto constant_count = reader.take<uint32_t>();
    const auto variant_count = reader.take<uint32_t>();
    require(constant_count == 24 && variant_count > 0 && variant_count <= 4 &&
                item.vertex_count > 0 && item.vertex_count % 4 == 0 &&
                item.vertex_count * 4 == byte_count && byte_count <= 32768 &&
                (metadata[4] & 0x03FFFFFC) == byte_count,
            "unsupported owned geometry");
    item.constants = reader.take<std::array<uint32_t, 96>>();
    item.vertices = reader.bytes(byte_count);
    for (uint32_t variant = 0; variant < variant_count; ++variant) {
      reader.take<uint64_t>();  // Dynamic-state identity.
      auto system = reader.take<std::array<uint32_t, 40>>();
      auto fetch = reader.take<std::array<uint32_t, 4>>();
      require(!(system[0] & 1) && system[4] == 0 && system[5] == 0 &&
                  (fetch[2] & 0x1FFFFFFC) == (metadata[3] & 0x1FFFFFFC) &&
                  (fetch[3] & 0x03FFFFFC) == byte_count,
              "unsupported vertex fetch state");
      if (variant == 0) {
        item.system = system;
        item.fetch = fetch;
      } else {
        require(fetch == item.fetch, "fetch changes across variants");
        for (size_t word = 0; word < system.size(); ++word)
          require(system[word] == item.system[word] || word == 33 || word == 37,
                  "non-viewport variant change");
      }
    }
    auto bits = [](uint32_t word) { return std::bit_cast<float>(word); };
    const float scale_y = bits(item.system[33]);
    const float offset_y = bits(item.system[37]);
    require(std::isfinite(scale_y) && scale_y > 0 && std::isfinite(offset_y) &&
                std::abs((offset_y + 1) / scale_y - 1 + 1.f / height) < 1e-6f &&
                bits(item.system[32]) == 1 && bits(item.system[34]) == -1 &&
                std::abs(bits(item.system[36]) - 1.f / width) < 1e-6f &&
                bits(item.system[38]) == 1,
            "viewport remap does not normalize to reference resolution");
    item.original_system = item.system;
    item.system[33] = std::bit_cast<uint32_t>(1.f);
    item.system[37] = std::bit_cast<uint32_t>(-1.f / height);
    item.fetch[2] &= 3;  // Rebase fetch 95 onto the private raw buffer.
    scene.items.push_back(std::move(item));
  }
  require(reader.position == file.size(), "trailing fixture bytes");
  return scene;
}

ComPtr<ID3D12Resource> buffer(ID3D12Device* device, uint64_t size,
                              D3D12_HEAP_TYPE heap, D3D12_RESOURCE_STATES state) {
  D3D12_HEAP_PROPERTIES properties{};
  properties.Type = heap;
  D3D12_RESOURCE_DESC description{};
  description.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
  description.Width = size;
  description.Height = description.DepthOrArraySize = description.MipLevels = 1;
  description.SampleDesc.Count = 1;
  description.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
  ComPtr<ID3D12Resource> resource;
  check(device->CreateCommittedResource(&properties, D3D12_HEAP_FLAG_NONE,
                                        &description, state, nullptr,
                                        IID_PPV_ARGS(&resource)));
  return resource;
}
ComPtr<ID3D12Resource> upload(ID3D12Device* device, const void* bytes, size_t size) {
  auto resource = buffer(device, (size + 255) & ~uint64_t(255),
                         D3D12_HEAP_TYPE_UPLOAD, D3D12_RESOURCE_STATE_GENERIC_READ);
  void* mapping = nullptr;
  D3D12_RANGE empty{};
  check(resource->Map(0, &empty, &mapping));
  std::memcpy(mapping, bytes, size);
  resource->Unmap(0, nullptr);
  return resource;
}
ComPtr<ID3D12Resource> texture(ID3D12Device* device, DXGI_FORMAT format,
                               D3D12_RESOURCE_FLAGS flags,
                               D3D12_RESOURCE_STATES initial,
                               const D3D12_CLEAR_VALUE& clear) {
  D3D12_HEAP_PROPERTIES properties{};
  properties.Type = D3D12_HEAP_TYPE_DEFAULT;
  D3D12_RESOURCE_DESC description{};
  description.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
  description.Width = width;
  description.Height = height;
  description.DepthOrArraySize = description.MipLevels = 1;
  description.Format = format;
  description.SampleDesc.Count = 1;
  description.Flags = flags;
  ComPtr<ID3D12Resource> resource;
  check(device->CreateCommittedResource(&properties, D3D12_HEAP_FLAG_NONE,
                                        &description, initial, &clear,
                                        IID_PPV_ARGS(&resource)));
  return resource;
}
void transition(ID3D12GraphicsCommandList* commands, ID3D12Resource* resource,
                D3D12_RESOURCE_STATES from, D3D12_RESOURCE_STATES to) {
  D3D12_RESOURCE_BARRIER barrier{};
  barrier.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
  barrier.Transition = {resource, D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES, from, to};
  commands->ResourceBarrier(1, &barrier);
}
}  // namespace

uint32_t pinyon_shift::native_renderer::RunSnr04OwnedSceneDiagnostic(
    const std::filesystem::path& fixture,
    const std::filesystem::path& vertex_shader,
    const std::filesystem::path& output_directory,
    ID3D12Device* borrowed_device) {
  const auto begin = std::chrono::steady_clock::now();
  auto scene = load_scene(fixture);
  auto vs = read(vertex_shader);
  require(vs.size() == 19328 && std::memcmp(vs.data(), "DXBC", 4) == 0 &&
              sha256(vs) == expected_vs_sha,
          "wrong vegetation vertex shader");
  const auto extracted = std::chrono::steady_clock::now();

  ComPtr<ID3D12Device> device;
  if (borrowed_device) {
    device = borrowed_device;
  } else {
    ComPtr<ID3D12Debug> debug;
    if (SUCCEEDED(D3D12GetDebugInterface(IID_PPV_ARGS(&debug))))
      debug->EnableDebugLayer();
    ComPtr<IDXGIFactory6> factory;
    check(CreateDXGIFactory2(0, IID_PPV_ARGS(&factory)));
    ComPtr<IDXGIAdapter1> adapter;
    check(factory->EnumAdapterByGpuPreference(0, DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE,
                                             IID_PPV_ARGS(&adapter)));
    check(D3D12CreateDevice(adapter.Get(), D3D_FEATURE_LEVEL_11_0,
                            IID_PPV_ARGS(&device)));
  }
  constexpr char ps_source[] =
      "cbuffer Item : register(b2) { uint id; };"
      "float4 main() : SV_Target0 {"
      " return float4((id & 255) / 255.0, ((id >> 8) & 255) / 255.0, 0, 1); }";
  ComPtr<ID3DBlob> ps, errors;
  check(D3DCompile(ps_source, sizeof(ps_source) - 1, nullptr, nullptr, nullptr,
                   "main", "ps_5_1", 0, 0, &ps, &errors));
  D3D12_ROOT_PARAMETER parameters[6]{};
  for (uint32_t i = 0; i < 4; ++i) {
    parameters[i].ParameterType =
        i == 3 ? D3D12_ROOT_PARAMETER_TYPE_SRV : D3D12_ROOT_PARAMETER_TYPE_CBV;
    parameters[i].Descriptor.ShaderRegister = i == 2 ? 3 : i == 3 ? 0 : i;
    parameters[i].ShaderVisibility = D3D12_SHADER_VISIBILITY_VERTEX;
  }
  parameters[4].ParameterType = D3D12_ROOT_PARAMETER_TYPE_32BIT_CONSTANTS;
  parameters[4].Constants.ShaderRegister = 2;
  parameters[4].Constants.Num32BitValues = 1;
  parameters[4].ShaderVisibility = D3D12_SHADER_VISIBILITY_PIXEL;
  parameters[5].ParameterType = D3D12_ROOT_PARAMETER_TYPE_UAV;
  parameters[5].Descriptor.ShaderRegister = 0;
  parameters[5].ShaderVisibility = D3D12_SHADER_VISIBILITY_VERTEX;
  D3D12_ROOT_SIGNATURE_DESC root_description{
      6, parameters, 0, nullptr,
      D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT |
          D3D12_ROOT_SIGNATURE_FLAG_ALLOW_STREAM_OUTPUT};
  ComPtr<ID3DBlob> root_blob;
  check(D3D12SerializeRootSignature(&root_description, D3D_ROOT_SIGNATURE_VERSION_1,
                                    &root_blob, &errors));
  ComPtr<ID3D12RootSignature> root;
  check(device->CreateRootSignature(0, root_blob->GetBufferPointer(),
                                    root_blob->GetBufferSize(), IID_PPV_ARGS(&root)));
  D3D12_GRAPHICS_PIPELINE_STATE_DESC pipeline_description{};
  pipeline_description.pRootSignature = root.Get();
  pipeline_description.VS = {vs.data(), vs.size()};
  pipeline_description.PS = {ps->GetBufferPointer(), ps->GetBufferSize()};
  pipeline_description.SampleMask = UINT_MAX;
  pipeline_description.RasterizerState.FillMode = D3D12_FILL_MODE_SOLID;
  pipeline_description.RasterizerState.CullMode = D3D12_CULL_MODE_NONE;
  pipeline_description.RasterizerState.DepthClipEnable = TRUE;
  pipeline_description.BlendState.RenderTarget[0].RenderTargetWriteMask =
      D3D12_COLOR_WRITE_ENABLE_ALL;
  pipeline_description.DepthStencilState.DepthEnable = TRUE;
  pipeline_description.DepthStencilState.DepthWriteMask = D3D12_DEPTH_WRITE_MASK_ALL;
  pipeline_description.DepthStencilState.DepthFunc = D3D12_COMPARISON_FUNC_GREATER_EQUAL;
  pipeline_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
  pipeline_description.NumRenderTargets = 1;
  pipeline_description.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM;
  pipeline_description.DSVFormat = DXGI_FORMAT_D32_FLOAT;
  pipeline_description.SampleDesc.Count = 1;
  ComPtr<ID3D12PipelineState> pipeline;
  auto pipeline_result = device->CreateGraphicsPipelineState(
      &pipeline_description, IID_PPV_ARGS(&pipeline));
  if (FAILED(pipeline_result)) {
    ComPtr<ID3D12InfoQueue> messages;
    if (SUCCEEDED(device.As(&messages))) {
      for (UINT64 i = 0; i < messages->GetNumStoredMessages(); ++i) {
        SIZE_T size = 0;
        messages->GetMessage(i, nullptr, &size);
        std::vector<char> storage(size);
        auto* message = reinterpret_cast<D3D12_MESSAGE*>(storage.data());
        if (SUCCEEDED(messages->GetMessage(i, message, &size)))
          std::cerr << message->pDescription << '\n';
      }
    }
    check(pipeline_result);
  }
  D3D12_SO_DECLARATION_ENTRY position_declaration{0, "SV_Position", 0, 0, 4, 0};
  UINT position_stride = 16;
  auto stream_description = pipeline_description;
  stream_description.PS = {};
  stream_description.StreamOutput = {&position_declaration, 1, &position_stride, 1,
                                     D3D12_SO_NO_RASTERIZED_STREAM};
  stream_description.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_POINT;
  stream_description.NumRenderTargets = 0;
  stream_description.RTVFormats[0] = DXGI_FORMAT_UNKNOWN;
  stream_description.DSVFormat = DXGI_FORMAT_UNKNOWN;
  stream_description.DepthStencilState.DepthEnable = FALSE;
  ComPtr<ID3D12PipelineState> stream_pipeline;
  auto stream_result = device->CreateGraphicsPipelineState(
      &stream_description, IID_PPV_ARGS(&stream_pipeline));
  if (FAILED(stream_result)) {
    ComPtr<ID3D12InfoQueue> messages;
    if (SUCCEEDED(device.As(&messages))) {
      for (UINT64 i = 0; i < messages->GetNumStoredMessages(); ++i) {
        SIZE_T size = 0;
        messages->GetMessage(i, nullptr, &size);
        std::vector<char> storage(size);
        auto* message = reinterpret_cast<D3D12_MESSAGE*>(storage.data());
        if (SUCCEEDED(messages->GetMessage(i, message, &size)))
          std::cerr << message->pDescription << '\n';
      }
    }
    check(stream_result);
  }

  D3D12_CLEAR_VALUE color_clear{};
  color_clear.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
  D3D12_CLEAR_VALUE depth_clear{};
  depth_clear.Format = DXGI_FORMAT_D32_FLOAT;
  depth_clear.DepthStencil.Depth = 0;
  auto color = texture(device.Get(), color_clear.Format,
                       D3D12_RESOURCE_FLAG_ALLOW_RENDER_TARGET,
                       D3D12_RESOURCE_STATE_RENDER_TARGET, color_clear);
  auto depth = texture(device.Get(), depth_clear.Format,
                       D3D12_RESOURCE_FLAG_ALLOW_DEPTH_STENCIL,
                       D3D12_RESOURCE_STATE_DEPTH_WRITE, depth_clear);
  D3D12_DESCRIPTOR_HEAP_DESC rtv_description{};
  rtv_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
  rtv_description.NumDescriptors = 1;
  ComPtr<ID3D12DescriptorHeap> rtv;
  check(device->CreateDescriptorHeap(&rtv_description, IID_PPV_ARGS(&rtv)));
  device->CreateRenderTargetView(color.Get(), nullptr, rtv->GetCPUDescriptorHandleForHeapStart());
  D3D12_DESCRIPTOR_HEAP_DESC dsv_description{};
  dsv_description.Type = D3D12_DESCRIPTOR_HEAP_TYPE_DSV;
  dsv_description.NumDescriptors = 1;
  ComPtr<ID3D12DescriptorHeap> dsv;
  check(device->CreateDescriptorHeap(&dsv_description, IID_PPV_ARGS(&dsv)));
  device->CreateDepthStencilView(depth.Get(), nullptr, dsv->GetCPUDescriptorHandleForHeapStart());

  auto max_vertices = std::max_element(scene.items.begin(), scene.items.end(),
                                       [](const Item& a, const Item& b) {
                                         return a.vertex_count < b.vertex_count;
                                       })->vertex_count;
  require(max_vertices <= UINT16_MAX, "index range exceeds 16 bits");
  std::vector<uint16_t> indices;
  indices.reserve(max_vertices / 4 * 6);
  for (uint32_t first = 0; first < max_vertices; first += 4)
    for (uint32_t corner : {0u, 1u, 3u, 1u, 2u, 3u})
      indices.push_back(uint16_t(first + corner));
  auto index_buffer = upload(device.Get(), indices.data(), indices.size() * sizeof(uint16_t));
  struct Resources { ComPtr<ID3D12Resource> vertices, b0, b0_original, b1, b3; };
  std::vector<Resources> owned;
  owned.reserve(scene.items.size());
  for (const auto& item : scene.items) {
    std::array<uint32_t, 120> system{};
    std::copy(item.system.begin(), item.system.end(), system.begin());
    std::array<uint32_t, 120> original_system{};
    std::copy(item.original_system.begin(), item.original_system.end(),
              original_system.begin());
    std::array<uint32_t, 192> fetch{};
    std::copy(item.fetch.begin(), item.fetch.end(), fetch.begin() + 188);
    owned.push_back({upload(device.Get(), item.vertices.data(), item.vertices.size()),
                     upload(device.Get(), system.data(), sizeof(system)),
                     upload(device.Get(), original_system.data(), sizeof(original_system)),
                     upload(device.Get(), item.constants.data(), 23 * 16),
                     upload(device.Get(), fetch.data(), sizeof(fetch))});
  }
  const auto built = std::chrono::steady_clock::now();

  D3D12_PLACED_SUBRESOURCE_FOOTPRINT color_layout{}, depth_layout{};
  uint64_t color_bytes = 0, depth_bytes = 0;
  auto color_description = color->GetDesc(), depth_description = depth->GetDesc();
  device->GetCopyableFootprints(&color_description, 0, 1, 0, &color_layout,
                                nullptr, nullptr, &color_bytes);
  device->GetCopyableFootprints(&depth_description, 0, 1, 0, &depth_layout,
                                nullptr, nullptr, &depth_bytes);
  auto color_readback = buffer(device.Get(), color_bytes, D3D12_HEAP_TYPE_READBACK,
                               D3D12_RESOURCE_STATE_COPY_DEST);
  auto depth_readback = buffer(device.Get(), depth_bytes, D3D12_HEAP_TYPE_READBACK,
                               D3D12_RESOURCE_STATE_COPY_DEST);
  std::vector<uint64_t> position_offsets;
  uint64_t position_allocation = 0, position_bytes = 0;
  for (const auto& item : scene.items) {
    position_offsets.push_back(position_allocation);
    const auto bytes = uint64_t(item.vertex_count) * 16;
    position_allocation += bytes + 8;
    position_bytes += bytes;
  }
  auto position_output = buffer(device.Get(), position_allocation,
                                D3D12_HEAP_TYPE_DEFAULT, D3D12_RESOURCE_STATE_COPY_DEST);
  auto position_readback = buffer(device.Get(), position_allocation,
                                  D3D12_HEAP_TYPE_READBACK, D3D12_RESOURCE_STATE_COPY_DEST);
  const std::vector<char> zero_positions(position_allocation);
  auto position_zero = upload(device.Get(), zero_positions.data(), zero_positions.size());
  ComPtr<ID3D12CommandQueue> queue;
  D3D12_COMMAND_QUEUE_DESC queue_description{};
  check(device->CreateCommandQueue(&queue_description, IID_PPV_ARGS(&queue)));
  ComPtr<ID3D12CommandAllocator> allocator;
  check(device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT,
                                       IID_PPV_ARGS(&allocator)));
  ComPtr<ID3D12GraphicsCommandList> commands;
  check(device->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT,
                                  allocator.Get(), pipeline.Get(),
                                  IID_PPV_ARGS(&commands)));
  auto rtv_handle = rtv->GetCPUDescriptorHandleForHeapStart();
  auto dsv_handle = dsv->GetCPUDescriptorHandleForHeapStart();
  constexpr float clear_color[4]{};
  commands->ClearRenderTargetView(rtv_handle, clear_color, 0, nullptr);
  commands->ClearDepthStencilView(dsv_handle, D3D12_CLEAR_FLAG_DEPTH, 0, 0, 0, nullptr);
  commands->OMSetRenderTargets(1, &rtv_handle, FALSE, &dsv_handle);
  D3D12_VIEWPORT viewport{0, 0, float(width), float(height), 0, 0.5f};
  D3D12_RECT scissor{0, 0, LONG(width), LONG(height)};
  commands->RSSetViewports(1, &viewport);
  commands->RSSetScissorRects(1, &scissor);
  commands->SetGraphicsRootSignature(root.Get());
  commands->SetPipelineState(pipeline.Get());
  commands->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
  D3D12_INDEX_BUFFER_VIEW index_view{index_buffer->GetGPUVirtualAddress(),
                                     UINT(indices.size() * sizeof(uint16_t)),
                                     DXGI_FORMAT_R16_UINT};
  commands->IASetIndexBuffer(&index_view);
  for (size_t ordinal = 0; ordinal < scene.items.size(); ++ordinal) {
    const auto& item = scene.items[ordinal];
    const auto& resource = owned[ordinal];
    commands->SetGraphicsRootConstantBufferView(0, resource.b0->GetGPUVirtualAddress());
    commands->SetGraphicsRootConstantBufferView(1, resource.b1->GetGPUVirtualAddress());
    commands->SetGraphicsRootConstantBufferView(2, resource.b3->GetGPUVirtualAddress());
    commands->SetGraphicsRootShaderResourceView(3, resource.vertices->GetGPUVirtualAddress());
    commands->SetGraphicsRoot32BitConstant(4, UINT(ordinal + 1), 0);
    commands->DrawIndexedInstanced(item.vertex_count / 4 * 6, 1, 0, 0, 0);
  }
  commands->CopyBufferRegion(position_output.Get(), 0, position_zero.Get(), 0,
                             position_allocation);
  transition(commands.Get(), position_output.Get(), D3D12_RESOURCE_STATE_COPY_DEST,
             D3D12_RESOURCE_STATE_STREAM_OUT);
  commands->SetPipelineState(stream_pipeline.Get());
  commands->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_POINTLIST);
  for (size_t ordinal = 0; ordinal < scene.items.size(); ++ordinal) {
    const auto& resource = owned[ordinal];
    const auto bytes = uint64_t(scene.items[ordinal].vertex_count) * 16;
    const auto address = position_output->GetGPUVirtualAddress() + position_offsets[ordinal];
    commands->SetGraphicsRootConstantBufferView(0, resource.b0_original->GetGPUVirtualAddress());
    commands->SetGraphicsRootConstantBufferView(1, resource.b1->GetGPUVirtualAddress());
    commands->SetGraphicsRootConstantBufferView(2, resource.b3->GetGPUVirtualAddress());
    commands->SetGraphicsRootShaderResourceView(3, resource.vertices->GetGPUVirtualAddress());
    D3D12_STREAM_OUTPUT_BUFFER_VIEW position_view{address, bytes, address + bytes};
    commands->SOSetTargets(0, 1, &position_view);
    commands->DrawInstanced(scene.items[ordinal].vertex_count, 1, 0, 0);
  }
  transition(commands.Get(), position_output.Get(), D3D12_RESOURCE_STATE_STREAM_OUT,
             D3D12_RESOURCE_STATE_COPY_SOURCE);
  commands->CopyResource(position_readback.Get(), position_output.Get());
  transition(commands.Get(), color.Get(), D3D12_RESOURCE_STATE_RENDER_TARGET,
             D3D12_RESOURCE_STATE_COPY_SOURCE);
  transition(commands.Get(), depth.Get(), D3D12_RESOURCE_STATE_DEPTH_WRITE,
             D3D12_RESOURCE_STATE_COPY_SOURCE);
  D3D12_TEXTURE_COPY_LOCATION source{}, destination{};
  source.Type = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
  destination.Type = D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;
  source.pResource = color.Get();
  destination.pResource = color_readback.Get();
  destination.PlacedFootprint = color_layout;
  commands->CopyTextureRegion(&destination, 0, 0, 0, &source, nullptr);
  source.pResource = depth.Get();
  destination.pResource = depth_readback.Get();
  destination.PlacedFootprint = depth_layout;
  commands->CopyTextureRegion(&destination, 0, 0, 0, &source, nullptr);
  check(commands->Close());
  ID3D12CommandList* lists[]{commands.Get()};
  queue->ExecuteCommandLists(1, lists);
  ComPtr<ID3D12Fence> fence;
  check(device->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence)));
  check(queue->Signal(fence.Get(), 1));
  HANDLE event = CreateEvent(nullptr, FALSE, FALSE, nullptr);
  require(event != nullptr, "CreateEvent failed");
  auto wait_result = fence->SetEventOnCompletion(1, event);
  auto waited = SUCCEEDED(wait_result) ? WaitForSingleObject(event, 30000) : WAIT_FAILED;
  CloseHandle(event);
  check(wait_result);
  require(waited == WAIT_OBJECT_0, "GPU wait failed");
  check(device->GetDeviceRemovedReason());
  ComPtr<ID3D12InfoQueue> messages;
  if (SUCCEEDED(device.As(&messages))) {
    for (UINT64 i = 0; i < messages->GetNumStoredMessages(); ++i) {
      SIZE_T size = 0;
      check(messages->GetMessage(i, nullptr, &size));
      std::vector<char> storage(size);
      auto* message = reinterpret_cast<D3D12_MESSAGE*>(storage.data());
      check(messages->GetMessage(i, message, &size));
      require(message->Severity > D3D12_MESSAGE_SEVERITY_ERROR,
              message->pDescription);
    }
  }
  const auto drawn = std::chrono::steady_clock::now();

  std::filesystem::create_directories(output_directory);
  const auto& directory = output_directory;
  std::ofstream image(directory / "identity.ppm", std::ios::binary);
  image << "P6\n" << width << ' ' << height << "\n255\n";
  std::ofstream depth_file(directory / "depth.f32", std::ios::binary);
  std::ofstream positions_file(directory / "postvs.f32x4", std::ios::binary);
  void* positions = nullptr;
  D3D12_RANGE position_range{0, SIZE_T(position_allocation)};
  check(position_readback->Map(0, &position_range, &positions));
  for (size_t ordinal = 0; ordinal < scene.items.size(); ++ordinal) {
    const auto bytes = uint64_t(scene.items[ordinal].vertex_count) * 16;
    const auto* segment = static_cast<const char*>(positions) + position_offsets[ordinal];
    uint64_t positions_written = 0;
    std::memcpy(&positions_written, segment + bytes, 8);
    require(positions_written == bytes, "incomplete post-VS stream output");
    positions_file.write(segment, bytes);
  }
  position_readback->Unmap(0, nullptr);
  positions_file.close();
  require(bool(positions_file), "post-VS output write failed");
  uint32_t covered = 0;
  std::vector<uint32_t> item_pixels(scene.items.size());
  void *colors = nullptr, *depths = nullptr;
  D3D12_RANGE color_range{0, SIZE_T(color_bytes)}, depth_range{0, SIZE_T(depth_bytes)};
  check(color_readback->Map(0, &color_range, &colors));
  check(depth_readback->Map(0, &depth_range, &depths));
  for (uint32_t y = 0; y < height; ++y) {
    auto* color_row = static_cast<const uint8_t*>(colors) + y * color_layout.Footprint.RowPitch;
    auto* depth_row = reinterpret_cast<const float*>(
        static_cast<const uint8_t*>(depths) + y * depth_layout.Footprint.RowPitch);
    for (uint32_t x = 0; x < width; ++x) {
      const auto* pixel = color_row + x * 4;
      image.write(reinterpret_cast<const char*>(pixel), 3);
      const auto id = uint32_t(pixel[0]) | (uint32_t(pixel[1]) << 8);
      if (id) {
        require(id <= scene.items.size() && std::isfinite(depth_row[x]) &&
                    depth_row[x] > 0 && depth_row[x] <= 1,
                "invalid covered pixel/depth");
        ++covered;
        ++item_pixels[id - 1];
      }
    }
    depth_file.write(reinterpret_cast<const char*>(depth_row), width * sizeof(float));
  }
  D3D12_RANGE empty{};
  color_readback->Unmap(0, &empty);
  depth_readback->Unmap(0, &empty);
  image.close();
  depth_file.close();
  require(bool(image) && bool(depth_file), "diagnostic output write failed");
  const auto complete = std::chrono::steady_clock::now();
  auto us = [](auto from, auto to) {
    return std::chrono::duration_cast<std::chrono::microseconds>(to - from).count();
  };
  std::ofstream summary(directory / "summary.json");
  summary << "{\"schema\":\"pinyon-shift.snr04-owned-diagnostic.v1\","
          << "\"label\":\"private unmasked geometry diagnostic, not compatibility or FPS\","
          << "\"source_frame\":" << scene.source_frame << ','
          << "\"fixture_sha256\":\"" << scene.fixture_sha256 << "\","
          << "\"vs_sha256\":\"" << expected_vs_sha << "\","
          << "\"depth_test\":\"greater_equal\","
          << "\"depth_viewport\":[0,0.5],"
          << "\"width\":" << width << ",\"height\":" << height << ','
          << "\"items\":" << scene.items.size() << ','
          << "\"covered_pixels\":" << covered << ','
          << "\"visible_items\":"
          << std::count_if(item_pixels.begin(), item_pixels.end(),
                           [](uint32_t value) { return value != 0; }) << ','
          << "\"postvs_bytes\":" << position_bytes << ','
          << "\"extract_us\":" << us(begin, extracted) << ','
          << "\"build_us\":" << us(extracted, built) << ','
          << "\"draw_readback_us\":" << us(built, drawn) << ','
          << "\"write_us\":" << us(drawn, complete) << ','
          << "\"item_pixels\":[";
  for (size_t ordinal = 0; ordinal < scene.items.size(); ++ordinal) {
    if (ordinal) summary << ',';
    summary << "{\"packet\":" << scene.items[ordinal].packet
            << ",\"pixels\":" << item_pixels[ordinal] << '}';
  }
  summary << "]}\n";
  summary.close();
  require(bool(summary) && covered > 0, "empty or unwritable diagnostic");
  return covered;
}
