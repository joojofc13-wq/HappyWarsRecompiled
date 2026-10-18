#include "local_title_storage.h"
#include <chrono>
#include <cstdio>

int main(int argc,char** argv) try {
  if(argc!=2) return 1;
  const auto path=std::filesystem::path(argv[1]).concat("."+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
  const std::string root="/users/xuid(2533274790395905)/storage/titlestorage/titlegroups/be554af1-2afa-4168-b64f-bdcb9ce7ac7b";
  const auto file=root+"/data/hw201209/slot0/player,binary";
  const auto other=root+"/data/hw201209/slot1/player,binary";
  const auto snapshot=root+"/data/hw201209/backup/0000/10/18/savedata/game_data.txt,binary";
  const std::vector<uint8_t> payload={0,1,255,0,42,0,17};
  {
    happywars::LocalTitleStorage service(path);
    if(service.request("GET",file).status!=404 || service.request("GET",root).status!=200) return 2;
    if(service.request("PUT",file,payload).status!=201 || service.request("GET",file).body!=payload) return 3;
    if(service.request("GET",other).status!=404 || service.request("PUT",other,{}).status!=201) return 4;
    if(service.request("PUT",snapshot,payload).status!=201 || service.request("GET",snapshot).body!=payload) return 12;
    auto listing=service.request("GET",root+"/data/hw201209/slot0/");
    if(listing.status!=200 || std::string(listing.body.begin(),listing.body.end()).find("player")==std::string::npos) return 5;
  }
  {
    happywars::LocalTitleStorage service(path);
    if(service.request("GET",file).body!=payload) return 6;
    if(service.request("GET",snapshot).body!=payload) return 13;
    const std::vector<uint8_t> replacement={5,0,4};
    if(service.request("PUT",file,replacement).status!=201 || service.request("GET",file).body!=replacement) return 7;
    if(service.request("DELETE",file).status!=200 || service.request("GET",file).status!=404 || service.request("GET",other).status!=200) return 8;
    if(service.request("GET",root+"/data/hw201209/slot0/../bad,binary").status!=400) return 9;
    if(service.request("GET","/users/xuid(123)/gamercard").status!=403) return 10;
    for(const auto invalid:{"backup/0000/10/18/../bad", "backup/0000/10/18/%2e%2e/bad", "backup/0000/10/bad", "backup/abcd/10/18/bad"})
      if(service.request("PUT",root+"/data/hw201209/"+invalid+",binary",payload).status!=400) return 14;
    if(service.request("PUT",snapshot,replacement).status!=201 || service.request("GET",snapshot).body!=replacement ||
        service.request("GET",other).status!=200) return 15;
    if(service.request("DELETE",snapshot).status!=200 || service.request("GET",snapshot).status!=404 ||
        service.request("GET",other).status!=200) return 16;
  }
  std::filesystem::remove(path);
  std::filesystem::remove(path.string()+".bak");
  std::puts("PASS title storage: opaque save bytes, slot isolation, restart, replacement, deletion and invalid routes");
} catch(const std::exception& error) {
  std::fprintf(stderr,"Title storage test failed: %s\n",error.what());
  return 11;
}
