// TU46 local ticket view. Balances come from the loaded game's save counters.
// No remote purchase status or marketplace receipt is fabricated.
#if defined(HAPPYWARS_TU46)
#include <rex/ppc.h>
#include <algorithm>
#include <atomic>
#include <bit>
#include <cstring>
#include <limits>

namespace {
uint32_t read(uint8_t* base,uint32_t address) {
  uint32_t value;std::memcpy(&value,base+address,4);return std::byteswap(value);
}
uint32_t profile(uint8_t* base) {
  // Original 830A1378 uses this title context; 82BC4F50 selects the user
  // inside the manager returned by 82888500.
  if(!base || !base[0x850d1374]) return 0;
  const auto user=read(base,0x850d1370),manager=read(base,0x84762e98);
  if(user>=4 || !manager) return 0;
  const uint64_t result=uint64_t(manager)+uint64_t(user)*0xa1298+0x10;
  return result+0x136cc<=0x100000000ULL?uint32_t(result):0;
}
}

REX_HOOK_RAW(sub_830A1310) {
  ctx.r3.u64=profile(base)?1:0;
}

REX_HOOK_RAW(sub_830A1378) {
  const auto save=profile(base);
  if(!save) { ctx.r3.u64=0;return; }
  const auto granted=int32_t(read(base,save+0x2218));
  const auto cached=int32_t(read(base,save+0x136c8));
  const auto used=int32_t(read(base,save+0x2210));
  const auto balance=int64_t(granted)+cached-used;
  ctx.r3.u64=uint32_t(std::clamp<int64_t>(balance,0,std::numeric_limits<int32_t>::max()));
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<8)
    REXLOG_INFO("Local tickets: balance={}, granted={}, used={}",ctx.r3.u32,granted,used);
}
#endif
