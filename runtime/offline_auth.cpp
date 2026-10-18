// XAuth ABI boundaries documented by the Netplay implementation. No remote token.
#include <rex/ppc.h>
#include <bit>
#include <cstring>

REX_HOOK_RAW(__imp__XampXAuthStartup) {
  const auto address=ctx.r3.u32;
  if(!base || !address || uint64_t(address)+8>0x100000000ULL) {
    ctx.r3.u64=0x80158404; return;
  }
  uint32_t size;
  std::memcpy(&size,base+address,4);
  ctx.r3.u64=std::byteswap(size)==8?0:0x80158401;
  REXLOG_INFO("Local XAuth: startup result={:#x}",ctx.r3.u32);
}
REX_HOOK_RAW(__imp__XampXAuthShutdown) {
  const auto address=ctx.r3.u32;
  if(base && address && uint64_t(address)+4<=0x100000000ULL) {
    const auto complete=std::byteswap(uint32_t{1});
    std::memcpy(base+address,&complete,4);
  }
  ctx.r3.u64=0;
}
REX_HOOK_RAW(__imp__XampXAuthGetTitleBuffer) {
  ctx.r3.u64=0; // No remote title-authentication blob exists in this local port.
  REXLOG_INFO("Local XAuth: no remote title buffer; explicit null rather than stale argument pointer");
}
