// Virtual network identity for the in-process LIVE service, without remote peers.
#include <rex/ppc.h>
#include <atomic>
#include <cstring>

REX_HOOK_RAW(__imp__NetDll_XNetGetTitleXnAddr) {
  const auto address=ctx.r4.u32;
  if(!base || !address || uint64_t(address)+36>0x100000000ULL) {
    ctx.r3.u64=1;return; // XNET_GET_XNADDR_NONE
  }
  auto* out=base+address;
  std::memset(out,0,36);
  // XNADDR: local IPv4, online IPv4, online port, Ethernet ID, online identity.
  const uint8_t loopback[]={127,0,0,1};
  std::memcpy(out,loopback,4);std::memcpy(out+4,loopback,4);
  const uint8_t ethernet[]={0x02,0x48,0x57,0,0,1};
  std::memcpy(out+10,ethernet,6);
  // Ethernet + static address + online local service. Happy Wars explicitly
  // tests bit 0x80 before leaving its connection wait.
  ctx.r3.u64=0x86;
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1,std::memory_order_relaxed)<8)
    REXLOG_INFO("Local LIVE network: loopback identity ready, flags=0x86");
}
