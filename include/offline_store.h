#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

struct sqlite3;

namespace happywars {
// This stores exact serialized bytes. The game-specific serializer is not yet
// identified; these records are NOT a claim of inventory compatibility.
struct SaveRecord {
  std::string key;
  std::uint32_t codec_version;
  std::vector<std::uint8_t> bytes;
};

class OfflineStore {
 public:
  explicit OfflineStore(const std::filesystem::path& path);
  ~OfflineStore();
  OfflineStore(const OfflineStore&) = delete;
  OfflineStore& operator=(const OfflineStore&) = delete;
  std::string profile_id() const;
  std::int64_t revision() const;
  std::vector<SaveRecord> load() const;
  // Optimistic revision check and all records commit in one transaction.
  std::int64_t save(const std::vector<SaveRecord>& records, std::int64_t expected_revision);
  void backup(const std::filesystem::path& destination) const;
  // Restore explicitly through SQLite's backup API; preserves original profile.
  static void restore(const std::filesystem::path& backup, const std::filesystem::path& destination);
 private:
  sqlite3* db_ = nullptr;
  std::filesystem::path path_;
  void exec(const char* sql) const;
};
}
