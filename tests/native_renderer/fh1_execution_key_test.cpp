#include <cassert>

#include <rex/system/interfaces/graphics.h>

int main() {
  rex::system::GraphicsFh1ExecutionKey key;
  key.kind = rex::system::GraphicsFh1ExecutionKind::kCopyResolve;
  key.hazard_flags = 3;
  key.flags = 2;
  key.shader_state = 11;
  key.pipeline_state = 12;
  key.attachment_state = 13;
  key.resource_state = 14;
  key.dynamic_state = 15;
  key.operation_state = 16;
  key.identity = key.ComputeIdentity();

  const auto bytes = key.Serialize();
  rex::system::GraphicsFh1ExecutionKey decoded;
  assert(rex::system::GraphicsFh1ExecutionKey::Deserialize(bytes, decoded));
  assert(decoded == key);

  auto invalid = bytes;
  invalid[0] = uint8_t(key.version + 1);
  assert(!rex::system::GraphicsFh1ExecutionKey::Deserialize(invalid, decoded));
  invalid = bytes;
  invalid.back() ^= 1;
  assert(!rex::system::GraphicsFh1ExecutionKey::Deserialize(invalid, decoded));
}
