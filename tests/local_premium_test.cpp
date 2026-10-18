#include <rex/ppc.h>
#include <windows.h>
REX_EXTERN(sub_82BAC790);
REX_EXTERN(sub_82F5C320);
int main() {
  uint8_t dummy = 0;
  PPCContext ctx{};
  for (unsigned user = 0; user < 4; ++user) {
    ctx.r3.u64 = user;
    sub_82F5C320(ctx, &dummy);
    if (ctx.r3.u32 != 1) return 1;
  }
  ctx.r3.u64 = 4; sub_82F5C320(ctx, &dummy); if (ctx.r3.u32) return 2;
  ctx.r3.u64 = 0; sub_82F5C320(ctx, nullptr); if (ctx.r3.u32) return 3;
  ctx.r3.u64 = 0; sub_82BAC790(ctx, &dummy); if (ctx.r3.u64) return 4;
  ctx.r3.u64 = 0xfffffff0; sub_82BAC790(ctx, &dummy); if (ctx.r3.u64) return 5;
  FILETIME time; GetSystemTimeAsFileTime(&time);
  const uint64_t now = (uint64_t(time.dwHighDateTime) << 32) | time.dwLowDateTime;
  ctx.r3.u64 = 0x10000010; ctx.r4.u64 = 0x123456789abcdef0ULL;
  sub_82BAC790(ctx, &dummy);
  if (ctx.r3.u64 <= now + 99ULL * 365 * 24 * 60 * 60 * 10000000 ||
      ctx.r4.u64 != 0x123456789abcdef0ULL) return 6;
}
