// TU46 CRT fast paths. Fall back for overlapping copies and non-RAM ranges.
#if defined(HAPPYWARS_TU46)
#include <rex/ppc.h>
#include <cstring>

REX_EXTERN(__imp__sub_83998350);
REX_EXTERN(__imp__sub_83999390);

namespace {
bool ram(uint32_t address, uint32_t size) {
  const uint64_t end=uint64_t(address)+size;
  if (!address || end>0x100000000ULL) return false;
  if (address<0x80000000u && end>0x7F000000u) return false;
  // Windows physical-memory aliases at E0000000 have a 4 KiB host offset.
  // A range crossing the alias boundary must use original per-access mapping.
  return address>=0xE0000000u || end<=0xE0000000u;
}
uint8_t* pointer(uint8_t* base, uint32_t address) {
  return base+address+(address>=0xE0000000u?0x1000u:0u);
}
}

REX_HOOK_RAW(sub_83998350) {
  const auto destination=ctx.r3.u32, size=ctx.r5.u32;
  if (!size) return;
  if (!base || !ram(destination,size)) {
    __imp__sub_83998350(ctx,base);
    return;
  }
  std::memset(pointer(base,destination),ctx.r4.u8,size);
}

REX_HOOK_RAW(sub_83999390) {
  const auto destination=ctx.r3.u32, source=ctx.r4.u32, size=ctx.r5.u32;
  if (!size) return;
  if (!base || !ram(destination,size) || !ram(source,size) ||
      (uint64_t(destination)<uint64_t(source)+size &&
       uint64_t(source)<uint64_t(destination)+size)) {
    __imp__sub_83999390(ctx,base);
    return;
  }
  std::memcpy(pointer(base,destination),pointer(base,source),size);
}
#endif
