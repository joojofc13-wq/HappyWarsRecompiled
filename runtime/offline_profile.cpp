// Virtual LIVE-compatible identity, exclusively inside this local native port.
// No real account, credentials, remote subscription or remote session is used.
#include <rex/ppc.h>
#include <algorithm>
#include <atomic>
#include <bit>
#include <cstring>
namespace {
constexpr uint64_t kOfflineXuid=0xe000000000000001ULL;
constexpr uint64_t kOnlineXuid=0x0009000000000001ULL;
constexpr char kName[]="LocalPlayer";
constexpr uint32_t kInvalid=0x80070057, kNoUser=0x80070525;
bool span(uint8_t* base,uint32_t address,size_t bytes) {
  return base && address && uint64_t(address)+bytes<=0x100000000ULL;
}
template<typename T> void store(uint8_t* base,uint32_t address,T value) {
  value=std::byteswap(value);
  std::memcpy(base+address,&value,sizeof(value));
}
}
REX_HOOK_RAW(__imp__XamUserGetSigninState) {
  const auto user=ctx.r3.u32;
  ctx.r3.u64=user==0?2:0;
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<8)
    REXLOG_INFO("Virtual LIVE profile: sign-in user={} state={} (local service)",user,ctx.r3.u32);
}
REX_HOOK_RAW(__imp__XamUserGetXUID) {
  const auto user=ctx.r3.u32, mask=ctx.r4.u32, output=ctx.r5.u32;
  if(!span(base,output,8) || (mask!=1 && mask!=2 && mask!=3 && mask!=4 && mask!=7)) {
    ctx.r3.u64=kInvalid; return;
  }
  store<uint64_t>(base,output,0);
  if(user>=4) { ctx.r3.u64=kInvalid; return; }
  if(user || mask==4) { ctx.r3.u64=kNoUser; return; }
  store(base,output,(mask&2)?kOnlineXuid:kOfflineXuid);
  ctx.r3.u64=0;
}
REX_HOOK_RAW(__imp__XamUserGetSigninInfo) {
  const auto user=ctx.r3.u32, flags=ctx.r4.u32, output=ctx.r5.u32;
  if(!span(base,output,40)) { ctx.r3.u64=kInvalid; return; }
  std::memset(base+output,0,40);
  if(user) { ctx.r3.u64=kNoUser; return; }
  const auto xuid=(flags&1) || !(flags&2)?kOnlineXuid:kOfflineXuid;
  store(base,output,xuid);
  store<uint32_t>(base,output+8,1);
  store<uint32_t>(base,output+12,2);
  std::memcpy(base+output+24,kName,sizeof(kName));
  ctx.r3.u64=0;
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<8)
    REXLOG_INFO("Virtual LIVE profile: sign-in info flags={:#x}, identity={:#x}",flags,xuid);
}
REX_HOOK_RAW(__imp__XamUserGetMembershipTierFromXUID) {
  const auto xuid=ctx.r3.u64;
  ctx.r3.u64=(xuid==kOnlineXuid || xuid==kOfflineXuid)?6:0;
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<8)
    REXLOG_INFO("Virtual LIVE profile: membership query identity={:#x}, tier={}",xuid,ctx.r3.u32);
}
REX_HOOK_RAW(__imp__XamUserCheckPrivilege) {
  const auto user=ctx.r3.u32, permission=ctx.r4.u32, output=ctx.r5.u32;
  if(!span(base,output,4)) { ctx.r3.u64=87; return; }
  store<uint32_t>(base,output,0);
  if(user!=0 && user!=0xff) { ctx.r3.u64=user<4?1317:87; return; }
  store<uint32_t>(base,output,1);
  ctx.r3.u64=0;
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<16)
    REXLOG_INFO("Virtual LIVE profile: local permission {} granted for user={}",permission,user);
}
REX_HOOK_RAW(__imp__XamUserGetName) {
  const auto user=ctx.r3.u32, output=ctx.r4.u32, length=ctx.r5.u32;
  if(!length || !span(base,output,length) || user>=4) { ctx.r3.u64=87; return; }
  base[output]=0;
  if(user) { ctx.r3.u64=1317; return; }
  const auto count=std::min(size_t(length)-1,sizeof(kName)-1);
  std::memcpy(base+output,kName,count);
  base[output+count]=0;
  ctx.r3.u64=0;
}
