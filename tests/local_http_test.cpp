#include "local_http.h"
#include <rex/ppc.h>
#include <array>
#include <bit>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <vector>
REX_EXTERN(__imp__NetDll_XHttpOpen);
REX_EXTERN(__imp__NetDll_XHttpConnect);
REX_EXTERN(__imp__NetDll_XHttpOpenRequest);
REX_EXTERN(__imp__NetDll_XHttpSendRequest);
REX_EXTERN(__imp__NetDll_XHttpReceiveResponse);
REX_EXTERN(__imp__NetDll_XHttpQueryHeaders);
REX_EXTERN(__imp__NetDll_XHttpReadData);
REX_EXTERN(__imp__NetDll_XHttpCloseHandle);
REX_EXTERN(__imp__NetDll_XHttpDoWork);
REX_EXTERN(__imp__NetDll_XHttpShutdown);
REX_EXTERN(__imp__NetDll_XHttpCrackUrl);
REX_EXTERN(__imp__XamGetToken);
REX_EXTERN(__imp__XamFreeToken);
int main(int argc,char** argv) try {
  if(argc!=2) return 1;
  std::array<uint8_t,16384> memory{};
  auto* base=memory.data();
  auto write=[&](uint32_t p,uint32_t n){n=std::byteswap(n);std::memcpy(base+p,&n,4);};
  auto read=[&](uint32_t p){uint32_t n;std::memcpy(&n,base+p,4);return std::byteswap(n);};
  auto str=[&](uint32_t p,const std::string& s){std::memcpy(base+p,s.c_str(),s.size()+1);};
  const std::string origin="http://happywars.local:80";
  const std::string path="/users/xuid(2533274790395905)/storage/titlestorage/titlegroups/be554af1-2afa-4168-b64f-bdcb9ce7ac7b/data/hw201209/slot0/player,binary";
  const auto url=origin+path;
  str(256,url);
  PPCContext ctx{};
  ctx.r4.u64=256;ctx.r5.u64=url.size();ctx.r6.u64=0x90000000;ctx.r7.u64=64;
  write(64,60);write(80,1024);write(84,128);write(112,0xffffffff);
  __imp__NetDll_XHttpCrackUrl(ctx,base);
  if(ctx.r3.u32!=1 || std::strcmp(reinterpret_cast<char*>(base+1024),"happywars.local") ||
      read(76)!=1 || read(108)!=256+origin.size() || read(112)!=path.size() ||
      memory[88]!=0 || memory[89]!=80) return 2;
  ctx={};ctx.r4.u64=256;ctx.r5.u64=url.size();ctx.r6.u64=1200;
  write(1200,0xdeadbeef);
  __imp__XamGetToken(ctx,base);
  if(ctx.r3.u32 || read(1200)) return 3;
  str(256,"http://example.com/");
  ctx={};ctx.r4.u64=256;ctx.r5.u64=19;ctx.r6.u64=1200;
  __imp__XamGetToken(ctx,base);
  if(ctx.r3.u32!=87 || read(1200)) return 4;
  // A catalog URL must parse even though the transport never leaves the PC.
  const std::string catalog="https://catalog.example:8443/offers?locale=en-US";
  str(256,catalog);
  std::memset(base+64,0,60);write(64,60);
  write(80,1024);write(84,128);write(108,1500);write(112,64);
  write(116,1600);write(120,64);
  ctx={};ctx.r4.u64=256;ctx.r5.u64=catalog.size();ctx.r7.u64=64;
  __imp__NetDll_XHttpCrackUrl(ctx,base);
  if(ctx.r3.u32!=1 || read(76)!=2 || memory[88]!=0x20 || memory[89]!=0xfb ||
      std::strcmp(reinterpret_cast<char*>(base+1024),"catalog.example") ||
      std::strcmp(reinterpret_cast<char*>(base+1500),"/offers") ||
      std::strcmp(reinterpret_cast<char*>(base+1600),"?locale=en-US")) return 17;
  write(84,4);memory[1024]=0x5a;
  ctx={};ctx.r4.u64=256;ctx.r5.u64=catalog.size();ctx.r7.u64=64;
  __imp__NetDll_XHttpCrackUrl(ctx,base);
  if(ctx.r3.u32 || read(84)!=16 || memory[1024]!=0x5a) return 18;
  str(256,"https://catalog.example:99999/offers");
  ctx={};ctx.r4.u64=256;ctx.r5.u64=std::strlen(reinterpret_cast<char*>(base+256));ctx.r7.u64=64;
  __imp__NetDll_XHttpCrackUrl(ctx,base);
  if(ctx.r3.u32) return 19;
  str(1024,"happywars.local");
  str(256,url);
  const auto database=std::filesystem::path(argv[1]).concat("."+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
  uint32_t session=0,connection=0;
  auto open=[&]{
    ctx={};__imp__NetDll_XHttpOpen(ctx,base);session=ctx.r3.u32;
    ctx={};ctx.r4.u64=session;ctx.r5.u64=1024;__imp__NetDll_XHttpConnect(ctx,base);connection=ctx.r3.u32;
    return session && connection;
  };
  auto request=[&](const char* verb,const std::vector<uint8_t>& body){
    str(1300,verb);str(1400,path);
    ctx={};ctx.r4.u64=connection;ctx.r5.u64=1300;ctx.r6.u64=1400;
    __imp__NetDll_XHttpOpenRequest(ctx,base);const auto handle=ctx.r3.u32;
    if(!handle) return 0u;
    if(!body.empty()) std::memcpy(base+2048,body.data(),body.size());
    ctx={};ctx.r4.u64=handle;ctx.r7.u64=2048;ctx.r8.u64=body.size();ctx.r9.u64=body.size();
    __imp__NetDll_XHttpSendRequest(ctx,base);if(ctx.r3.u32!=1) return 0u;
    ctx={};__imp__NetDll_XHttpDoWork(ctx,base);if(ctx.r3.u32!=1) return 0u;
    ctx={};ctx.r4.u64=handle;__imp__NetDll_XHttpReceiveResponse(ctx,base);
    return ctx.r3.u32==1?handle:0u;
  };
  auto query=[&](uint32_t handle,uint32_t kind){
    write(3000,4);ctx={};ctx.r4.u64=handle;ctx.r5.u64=kind;ctx.r7.u64=3004;ctx.r8.u64=3000;
    __imp__NetDll_XHttpQueryHeaders(ctx,base);
    return ctx.r3.u32==1?read(3004):0u;
  };
  InitializeLocalHttp(database);if(!open()) return 5;
  auto h=request("GET",{});if(query(h,0x2000fffe)!=404) return 6;
  const std::vector<uint8_t> payload={0,255,1,0,42};
  h=request("PUT",payload);if(query(h,0x2000fffe)!=201) return 7;
  // Drop the service and handle state, then reopen the database.
  ctx={};__imp__NetDll_XHttpShutdown(ctx,base);
  InitializeLocalHttp(database);if(!open()) return 8;
  h=request("GET",{});if(query(h,0x2000fffe)!=200 || query(h,0x20000009)!=payload.size()) return 9;
  ctx={};ctx.r4.u64=h;ctx.r5.u64=4096;ctx.r6.u64=2;ctx.r7.u64=3000;
  __imp__NetDll_XHttpReadData(ctx,base);
  if(ctx.r3.u32!=1 || read(3000)!=2 || memory[4097]!=255) return 10;
  ctx={};ctx.r4.u64=h;ctx.r5.u64=4098;ctx.r6.u64=1024;ctx.r7.u64=3000;
  __imp__NetDll_XHttpReadData(ctx,base);
  if(ctx.r3.u32!=1 || read(3000)!=3 || std::memcmp(base+4096,payload.data(),payload.size())) return 11;
  str(1300,"ETag");write(3000,32);
  ctx={};ctx.r4.u64=h;ctx.r5.u64=0xffff;ctx.r6.u64=1300;ctx.r7.u64=3100;ctx.r8.u64=3000;
  __imp__NetDll_XHttpQueryHeaders(ctx,base);
  if(ctx.r3.u32!=1 || std::strcmp(reinterpret_cast<char*>(base+3100),"\"local\"")) return 12;
  ctx={};ctx.r4.u64=h;__imp__NetDll_XHttpCloseHandle(ctx,base);
  if(query(h,0x2000fffe)) return 13;
  h=request("PUT",{9,0});if(query(h,0x2000fffe)!=201) return 14;
  h=request("DELETE",{});if(query(h,0x2000fffe)!=200) return 15;
  ctx={};__imp__NetDll_XHttpShutdown(ctx,base);
  // Shutdown releases the SQLite connection before removing the fixture.
  std::filesystem::remove(database);std::filesystem::remove(database.string()+".bak");
  std::puts("PASS local HTTP guest ABI: URL, token policy, headers, binary reads, restart, replace and delete");
} catch(const std::exception& error) {
  std::fprintf(stderr,"HTTP test failed: %s\n",error.what());return 16;
}
