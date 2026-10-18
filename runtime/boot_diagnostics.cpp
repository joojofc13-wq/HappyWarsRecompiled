// Non-invasive tracing of original title checks; no results are changed here.
#include <rex/ppc.h>
#include <atomic>

REX_EXTERN(__imp__sub_82C16438);
REX_EXTERN(__imp__sub_82C1FC18);

REX_HOOK_RAW(sub_82C16438) {
  const auto flags=ctx.r3.u32;
  const auto user=ctx.r4.u32;
  __imp__sub_82C16438(ctx,base);
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<16)
    REXLOG_INFO("Title profile check: flags={:#x}, user={}, restriction={:#x}",flags,user,ctx.r3.u32);
}

REX_HOOK_RAW(sub_82C1FC18) {
  REXLOG_INFO("Title message: caller={:#x}, descriptor={:#x}, user={}, text={:#x}",
              uint32_t(ctx.lr),ctx.r3.u32,ctx.r4.u32,ctx.r5.u32);
  __imp__sub_82C1FC18(ctx,base);
}
