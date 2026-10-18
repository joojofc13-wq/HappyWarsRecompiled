// Synchronous service lookup used by the original title-storage callers.
#include <rex/ppc.h>
#include <cstring>
#include <atomic>
#include <string_view>
namespace {
constexpr char kUrl[]="http://happywars.local:80";
bool valid(uint8_t* base,uint32_t p,uint32_t size) {
  return base && p && uint64_t(p)+size<=0x100000000ULL;
}
}
REX_HOOK_RAW(sub_8388BF10) {
  const auto service=ctx.r3.u32,output=ctx.r4.u32,capacity=ctx.r5.u32;
  if(!valid(base,service,9) || !valid(base,output,capacity)) { ctx.r3.u64=87; return; }
  if(ctx.r6.u32) {
    static std::atomic<unsigned> calls{};
    if(calls.fetch_add(1)<16)
      REXLOG_WARN("Local endpoint: asynchronous lookup not implemented, caller={:#x}",ctx.lr);
    ctx.r3.u64=50; return;
  }
  if(std::memcmp(base+service,"services",9)) {
    static std::atomic<unsigned> calls{};
    if(calls.fetch_add(1)<16)
      REXLOG_WARN("Local endpoint: unsupported service prefix '{}', caller={:#x}",
        std::string_view(reinterpret_cast<char*>(base+service),8),ctx.lr);
    ctx.r3.u64=1168; return;
  }
  if(capacity<sizeof(kUrl)) { ctx.r3.u64=122; return; }
  std::memcpy(base+output,kUrl,sizeof(kUrl));
  ctx.r3.u64=0;
  REXLOG_INFO("Local endpoint: services -> {}",kUrl);
}
