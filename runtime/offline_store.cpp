#include "offline_store.h"
#include <winsqlite/winsqlite3.h>
#include <limits>
#include <memory>
#include <stdexcept>

namespace happywars {
namespace {
void check(sqlite3* db, int result) {
  if (result != SQLITE_OK && result != SQLITE_DONE && result != SQLITE_ROW)
    throw std::runtime_error(sqlite3_errmsg(db));
}
class Statement {
 public:
  sqlite3_stmt* value = nullptr;
  Statement(sqlite3* db, const char* sql) { check(db,sqlite3_prepare_v2(db,sql,-1,&value,nullptr)); }
  ~Statement() { sqlite3_finalize(value); }
};
std::string text(sqlite3_stmt* s, int index) {
  const auto* p = sqlite3_column_text(s,index);
  return p ? reinterpret_cast<const char*>(p) : "";
}
void copy_database(sqlite3* from, sqlite3* to) {
  auto* b = sqlite3_backup_init(to,"main",from,"main");
  if (!b) throw std::runtime_error(sqlite3_errmsg(to));
  const int step = sqlite3_backup_step(b,-1);
  const int finish = sqlite3_backup_finish(b);
  if (step != SQLITE_DONE) throw std::runtime_error("SQLite backup did not complete");
  check(to,finish);
}
}

void OfflineStore::exec(const char* sql) const {
  char* message = nullptr;
  int result = sqlite3_exec(db_,sql,nullptr,nullptr,&message);
  std::string error = message ? message : "SQLite error";
  sqlite3_free(message);
  if (result != SQLITE_OK) throw std::runtime_error(error);
}

OfflineStore::OfflineStore(const std::filesystem::path& path) : path_(std::filesystem::absolute(path)) {
  std::filesystem::create_directories(path_.parent_path());
  const auto utf8 = path_.u8string();
  const int result = sqlite3_open_v2(reinterpret_cast<const char*>(utf8.c_str()), &db_,
      SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE|SQLITE_OPEN_FULLMUTEX,nullptr);
  try {
    check(db_,result);
    sqlite3_busy_timeout(db_,5000);
    Statement integrity(db_,"PRAGMA quick_check");
    check(db_,sqlite3_step(integrity.value));
    if (text(integrity.value,0) != "ok") throw std::runtime_error("Corrupt save; restore a verified backup");
    Statement schema(db_,"PRAGMA user_version");
    check(db_,sqlite3_step(schema.value));
    const int version = sqlite3_column_int(schema.value,0);
    if (version > 1) throw std::runtime_error("Save schema newer than supported version 1");
    // Finalize read statements before changing journal mode.
    sqlite3_finalize(integrity.value); integrity.value=nullptr;
    sqlite3_finalize(schema.value); schema.value=nullptr;
    exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;");
    exec("BEGIN IMMEDIATE");
    exec("CREATE TABLE IF NOT EXISTS profile(singleton INTEGER PRIMARY KEY CHECK(singleton=1),"
         "id TEXT NOT NULL,revision INTEGER NOT NULL CHECK(revision>=0));"
         "CREATE TABLE IF NOT EXISTS records(key TEXT PRIMARY KEY,codec_version INTEGER NOT NULL CHECK(codec_version>0),"
         "payload BLOB NOT NULL);"
         "INSERT OR IGNORE INTO profile VALUES(1,lower(hex(randomblob(16))),0);"
         "PRAGMA user_version=1;");
    exec("COMMIT");
  } catch (...) {
    sqlite3_close(db_); db_=nullptr;
    throw;
  }
}

OfflineStore::~OfflineStore() { if (db_) sqlite3_close(db_); }

std::string OfflineStore::profile_id() const {
  Statement s(db_,"SELECT id FROM profile WHERE singleton=1");
  if (sqlite3_step(s.value)!=SQLITE_ROW) throw std::runtime_error("Profile missing");
  return text(s.value,0);
}

std::int64_t OfflineStore::revision() const {
  Statement s(db_,"SELECT revision FROM profile WHERE singleton=1");
  if (sqlite3_step(s.value)!=SQLITE_ROW) throw std::runtime_error("Profile missing");
  return sqlite3_column_int64(s.value,0);
}

std::vector<SaveRecord> OfflineStore::load() const {
  Statement s(db_,"SELECT key,codec_version,payload FROM records ORDER BY key");
  std::vector<SaveRecord> output;
  int rc;
  while ((rc=sqlite3_step(s.value))==SQLITE_ROW) {
    SaveRecord r{text(s.value,0),static_cast<std::uint32_t>(sqlite3_column_int64(s.value,1)),{}};
    const int size = sqlite3_column_bytes(s.value,2);
    const auto* bytes = static_cast<const std::uint8_t*>(sqlite3_column_blob(s.value,2));
    if (size) r.bytes.assign(bytes,bytes+size);
    output.push_back(std::move(r));
  }
  check(db_,rc);
  return output;
}

std::int64_t OfflineStore::save(const std::vector<SaveRecord>& records, std::int64_t expected) {
  exec("BEGIN IMMEDIATE");
  try {
    if (revision()!=expected) throw std::runtime_error("Concurrent save revision changed");
    if (expected==std::numeric_limits<std::int64_t>::max()) throw std::runtime_error("Revision exhausted");
    exec("DELETE FROM records");
    Statement s(db_,"INSERT INTO records(key,codec_version,payload) VALUES(?,?,?)");
    for (const auto& record : records) {
      if (record.key.empty() || record.codec_version==0 || record.bytes.size()>64*1024*1024)
        throw std::runtime_error("Invalid save record");
      check(db_,sqlite3_bind_text(s.value,1,record.key.c_str(),static_cast<int>(record.key.size()),SQLITE_TRANSIENT));
      check(db_,sqlite3_bind_int64(s.value,2,record.codec_version));
      const auto* bytes=record.bytes.empty() ? "" : reinterpret_cast<const char*>(record.bytes.data());
      check(db_,sqlite3_bind_blob(s.value,3,bytes,static_cast<int>(record.bytes.size()),SQLITE_TRANSIENT));
      check(db_,sqlite3_step(s.value));
      check(db_,sqlite3_reset(s.value));
      check(db_,sqlite3_clear_bindings(s.value));
    }
    exec("UPDATE profile SET revision=revision+1 WHERE singleton=1");
    exec("COMMIT");
    return expected+1;
  } catch (...) { sqlite3_exec(db_,"ROLLBACK",nullptr,nullptr,nullptr); throw; }
}

void OfflineStore::backup(const std::filesystem::path& destination) const {
  if (std::filesystem::exists(destination)) throw std::runtime_error("Backup destination already exists");
  OfflineStore target(destination);
  copy_database(db_,target.db_);
}

void OfflineStore::restore(const std::filesystem::path& source, const std::filesystem::path& destination) {
  if (!std::filesystem::is_regular_file(source)) throw std::runtime_error("Backup missing");
  if (std::filesystem::exists(destination) && std::filesystem::equivalent(source,destination))
    throw std::runtime_error("Restore paths are identical");
  OfflineStore from(source);
  OfflineStore to(destination);
  copy_database(from.db_,to.db_);
}
}
