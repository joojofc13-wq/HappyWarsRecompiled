// TU46 offline Premium policy. No remote subscription or receipt is issued.
#if defined(HAPPYWARS_TU46)
#include <rex/ppc.h>
#include <windows.h>
#include <atomic>

// The original membership predicate compares current FILETIME against the
// expiration returned by 82BAC790. Renew the local horizon on every read so
// membership never counts down to expiration between sessions.
REX_HOOK_RAW(sub_82BAC790) {
  const uint64_t object = ctx.r3.u32;
  if (!base || !object || object + 0x14440 > 0x100000000ULL) {
    ctx.r3.u64 = 0;
    return;
  }
  FILETIME time;
  GetSystemTimeAsFileTime(&time);
  const uint64_t now = (uint64_t(time.dwHighDateTime) << 32) | time.dwLowDateTime;
  constexpr uint64_t century = 100ULL * 366 * 24 * 60 * 60 * 10000000;
  ctx.r3.u64 = now + century;
  static std::atomic<bool> logged{};
  if (!logged.exchange(true)) REXLOG_INFO("Local Premium: permanent offline membership enabled");
}

REX_HOOK_RAW(sub_82F5C320) {
  ctx.r3.u64 = base && ctx.r3.u32 < 4 ? 1 : 0;
}
#endif
