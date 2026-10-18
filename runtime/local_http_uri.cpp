// URL and token boundaries for the in-process storage service.
#include <rex/ppc.h>
#include <bit>
#include <cstring>
#include <string_view>

namespace {
bool valid(uint8_t* base,uint32_t p,uint32_t size) {
  return base && p && uint64_t(p)+size<=0x100000000ULL;
}
uint32_t read(uint8_t* base,uint32_t p) {
  uint32_t n; std::memcpy(&n,base+p,4); return std::byteswap(n);
}
void write(uint8_t* base,uint32_t p,uint32_t n) {
  n=std::byteswap(n); std::memcpy(base+p,&n,4);
}
bool local(std::string_view url) {
  constexpr std::string_view origin="http://happywars.local";
  if(!url.starts_with(origin)) return false;
  url.remove_prefix(origin.size());
  if(url.starts_with(":80")) url.remove_prefix(3);
  return url.empty() || url.starts_with("/");
}
}

REX_HOOK_RAW(__imp__XamGetToken) {
  const auto user=ctx.r3.u32,url=ctx.r4.u32,length=ctx.r5.u32,output=ctx.r6.u32;
  if(!valid(base,output,4)) { ctx.r3.u64=87; return; }
  write(base,output,0);
  if(ctx.r7.u32) { ctx.r3.u64=50; return; }
  if(user || length>4096 || !valid(base,url,length) ||
      !local({reinterpret_cast<char*>(base+url),length})) { ctx.r3.u64=87; return; }
  // The original request pump explicitly permits a null token. Local dispatch
  // authenticates the synthetic profile itself and needs no authorization header.
  ctx.r3.u64=0;
}
REX_HOOK_RAW(__imp__XamFreeToken) {
  // This implementation never allocates a token.
  if(ctx.r3.u32) REXLOG_ERROR("Unexpected non-local token passed to local release");
  ctx.r3.u64=0;
}

REX_HOOK_RAW(__imp__NetDll_XHttpCrackUrl) {
  const auto url=ctx.r4.u32,length=ctx.r5.u32,components=ctx.r7.u32;
  if(length>4096 || !valid(base,url,length) || !valid(base,components,60) ||
      read(base,components)!=60) { ctx.r3.u64=0; return; }
  const std::string_view text(reinterpret_cast<char*>(base+url),length);
  if(!local(text)) { ctx.r3.u64=0; return; }
  constexpr uint32_t host_offset=7,host_length=sizeof("happywars.local")-1;
  const auto slash=text.find('/',host_offset);
  const auto path_length=slash==std::string_view::npos?0:uint32_t(text.size()-slash);
  const auto host=read(base,components+16),capacity=read(base,components+20);
  const auto path=read(base,components+44),path_capacity=read(base,components+48);
  if((host && (capacity<=host_length || !valid(base,host,host_length+1))) ||
      (path && (path_capacity<=path_length || !valid(base,path,path_length+1)))) {
    ctx.r3.u64=0; return;
  }
  if(host) std::memcpy(base+host,"happywars.local",host_length+1);
  else if(capacity) write(base,components+16,url+host_offset);
  if(path) {
    if(path_length) std::memcpy(base+path,text.data()+slash,path_length);
    base[path+path_length]=0;
  } else if(path_capacity) {
    write(base,components+44,url+(path_length?uint32_t(slash):length));
  }
  write(base,components+20,host_length);
  write(base,components+48,path_length);
  write(base,components+12,1); // HTTP; the original consumer uses 2 for HTTPS.
  const auto port=std::byteswap(uint16_t{80});
  std::memcpy(base+components+24,&port,2);
  ctx.r3.u64=1;
}
