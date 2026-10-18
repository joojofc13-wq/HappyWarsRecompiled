#pragma once
#include "offline_store.h"
#include <mutex>
#include <span>
#include <string_view>

namespace happywars {
struct LocalResponse {
  unsigned status;
  std::string content_type;
  std::vector<uint8_t> body;
};
// Stores the original game's serialized bytes. It does not invent inventory.
class LocalTitleStorage {
 public:
  explicit LocalTitleStorage(const std::filesystem::path& database);
  LocalResponse request(std::string_view method,std::string_view path,
                        std::span<const uint8_t> body={});
 private:
  void backup();
  OfflineStore store_;
  std::filesystem::path backup_;
  std::mutex mutex_;
};
}
