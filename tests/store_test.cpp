#include "offline_store.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <winsqlite/winsqlite3.h>
#include <cstdlib>
using namespace happywars;
void require(bool condition,const char* message) { if(!condition) throw std::runtime_error(message); }
int main(int argc,char** argv) {
  try {
    require(argc==3,"Usage: store_test phase database");
    const std::string phase=argv[1];
    const std::filesystem::path db=argv[2];
    if (phase=="write") {
      OfflineStore store(db);
      require(store.revision()==0,"new revision");
      require(store.save({{"test-exact-bytes",7,{0,255,128,1,0,2}},{"test-empty",1,{}}},0)==1,"commit");
      std::ofstream(db.string()+".profile")<<store.profile_id();
      store.backup(db.string()+".backup");
    } else if (phase=="crash") {
      sqlite3* handle=nullptr;
      require(sqlite3_open(db.string().c_str(),&handle)==SQLITE_OK,"open before crash");
      require(sqlite3_exec(handle,"BEGIN IMMEDIATE; DELETE FROM records;",nullptr,nullptr,nullptr)==SQLITE_OK,
          "uncommitted mutation before crash");
      // Simulate termination without destructors or COMMIT.
      std::_Exit(0);
    } else if (phase=="read") {
      OfflineStore store(db);
      std::string previous; std::ifstream(db.string()+".profile")>>previous;
      require(store.profile_id()==previous,"profile survives process restart");
      auto records=store.load();
      require(records.size()==2 && records[1].codec_version==7 &&
          records[1].bytes==std::vector<std::uint8_t>({0,255,128,1,0,2}),"exact restored bytes and codec");
      bool rejected=false;
      try { store.save({{"duplicate",1,{1}},{"duplicate",1,{2}}},1); } catch (...) { rejected=true; }
      require(rejected && store.revision()==1 && store.load().size()==2,"failed commit rolls back");
      rejected=false;
      try { store.save({},0); } catch (...) { rejected=true; }
      require(rejected && store.revision()==1,"stale writer rejected");
      OfflineStore other(db);
      other.save({},1);
      rejected=false;
      try { store.save({},1); } catch (...) { rejected=true; }
      require(rejected && store.revision()==2,"second connection conflict rejected");
    } else if (phase=="restore") {
      OfflineStore::restore(db.string()+".backup",db);
      OfflineStore store(db);
      require(store.revision()==1 && store.load().size()==2,"backup restores contents");
    } else if (phase=="corrupt" || phase=="future") {
      bool rejected=false;
      try { OfflineStore store(db); } catch (...) { rejected=true; }
      require(rejected,"corrupt save rejected");
    } else throw std::runtime_error("Unknown phase");
    std::cout<<"PASS "<<phase<<"\n";
    return 0;
  } catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
