// URL and token boundaries for the in-process storage service.
#include <rex/ppc.h>
#include <bit>
#include <atomic>
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
  if(ctx.r7.u32) {
    static std::atomic<unsigned> calls{};
    if(calls.fetch_add(1)<16)
      REXLOG_WARN("Local token: asynchronous request not implemented, caller={:#x}",ctx.lr);
    ctx.r3.u64=50; return;
  }
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
  // Parsing a URL does not connect to it. All XHTTP handles still dispatch
  // inside the process, including original catalog-service host names.
  const bool secure=text.starts_with("https://");
  if(!secure && !text.starts_with("http://")) { ctx.r3.u64=0; return; }
  const uint32_t host_offset=secure?8:7;
  const auto authority_end=text.find_first_of("/?#",host_offset);
  const uint32_t end=authority_end==text.npos?length:uint32_t(authority_end);
  auto authority=text.substr(host_offset,end-host_offset);
  if(authority.empty() || authority.find('@')!=authority.npos ||
      text.find_first_of("\r\n\t ")!=text.npos) { ctx.r3.u64=0; return; }
  uint32_t port_value=secure?443:80;
  const auto colon=authority.find(':');
  if(colon!=authority.npos) {
    const auto port_text=authority.substr(colon+1);
    port_value=0;
    if(port_text.empty()) { ctx.r3.u64=0; return; }
    for(const char digit:port_text) {
      if(digit<'0' || digit>'9' || port_value>6553) { ctx.r3.u64=0; return; }
      port_value=port_value*10+uint32_t(digit-'0');
    }
    if(!port_value || port_value>65535) { ctx.r3.u64=0; return; }
    authority=authority.substr(0,colon);
  }
  if(authority.empty()) { ctx.r3.u64=0; return; }
  const auto extra_start=text.find_first_of("?#",end);
  const uint32_t path_end=extra_start==text.npos?length:uint32_t(extra_start);
  // Without an extra-info output request, XHTTP includes the query in the path.
  const bool separate_extra=read(base,components+52) || read(base,components+56);
  const uint32_t path_length=(separate_extra?path_end:length)-end;
  struct Part { uint32_t field,offset,size; };
  const Part parts[]={
    {4,0,secure?5u:4u},{16,host_offset,uint32_t(authority.size())},
    {28,end,0},{36,end,0},{44,end,path_length},
    {52,path_end,separate_extra?length-path_end:0}};
  bool fits=true;
  for(const auto& part:parts) {
    const auto output=read(base,components+part.field),capacity=read(base,components+part.field+4);
    if(output && (capacity<=part.size || !valid(base,output,part.size+1))) {
      write(base,components+part.field+4,part.size+1); fits=false;
    }
  }
  if(!fits) { ctx.r3.u64=0; return; }
  for(const auto& part:parts) {
    const auto output=read(base,components+part.field),capacity=read(base,components+part.field+4);
    if(output) {
      if(part.size) std::memmove(base+output,text.data()+part.offset,part.size);
      base[output+part.size]=0;
    } else if(capacity) write(base,components+part.field,url+part.offset);
    write(base,components+part.field+4,part.size);
  }
  write(base,components+12,secure?2:1);
  const auto port=std::byteswap(uint16_t(port_value));
  std::memcpy(base+components+24,&port,2);
  if(!local(text)) {
    static std::atomic<unsigned> calls{};
    if(calls.fetch_add(1)<16)
      REXLOG_INFO("Local URL: original host '{}' parsed for in-process transport, caller={:#x}",authority,ctx.lr);
  }
  ctx.r3.u64=1;
}
