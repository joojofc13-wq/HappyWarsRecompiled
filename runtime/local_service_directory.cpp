// Synchronous service lookup used by the original title-storage callers.
#include <rex/ppc.h>
#include <cstring>
namespace {
constexpr char kUrl[]="http://happywars.local:80";
bool valid(uint8_t* base,uint32_t p,uint32_t size) {
  return base && p && uint64_t(p)+size<=0x100000000ULL;
}
}
REX_HOOK_RAW(sub_832C0900) {
  const auto service=ctx.r3.u32,output=ctx.r4.u32,capacity=ctx.r5.u32;
  if(!valid(base,service,9) || !valid(base,output,capacity)) { ctx.r3.u64=87; return; }
  if(ctx.r6.u32) { ctx.r3.u64=50; return; }
  if(std::memcmp(base+service,"services",9)) { ctx.r3.u64=1168; return; }
  if(capacity<sizeof(kUrl)) { ctx.r3.u64=122; return; }
  std::memcpy(base+output,kUrl,sizeof(kUrl));
  ctx.r3.u64=0;
  REXLOG_INFO("Local endpoint: services -> {}",kUrl);
}
