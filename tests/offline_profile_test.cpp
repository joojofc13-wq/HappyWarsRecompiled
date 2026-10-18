#include <rex/ppc.h>
#include <array>
#include <bit>
#include <cstring>
#include <cstdio>
REX_EXTERN(__imp__XamUserGetSigninState);
REX_EXTERN(__imp__XamUserGetSigninInfo);
REX_EXTERN(__imp__XamUserGetXUID);
REX_EXTERN(__imp__XamUserGetMembershipTierFromXUID);
REX_EXTERN(__imp__XamUserCheckPrivilege);
REX_EXTERN(__imp__XamUserGetName);
int main() {
  alignas(16) std::array<uint8_t,256> memory{};
  auto* base=memory.data();
  auto read32=[&](unsigned offset) { uint32_t value; std::memcpy(&value,base+offset,4); return std::byteswap(value); };
  auto read64=[&](unsigned offset) { uint64_t value; std::memcpy(&value,base+offset,8); return std::byteswap(value); };
  for(uint32_t user:{0u,1u,3u,4u,0xffu}) {
    PPCContext ctx{}; ctx.r3.u64=user; ctx.r6.u64=0x12345678;
    __imp__XamUserGetSigninState(ctx,base);
    if(ctx.r3.u32!=(user?0u:2u) || ctx.r6.u64!=0x12345678) return 1;
  }
  for(uint32_t flags:{0u,1u,2u,3u}) {
    PPCContext ctx{}; ctx.r4.u64=flags; ctx.r5.u64=32;
    __imp__XamUserGetSigninInfo(ctx,base);
    if(ctx.r3.u32 || read32(40)!=1 || read32(44)!=2 ||
       std::strcmp(reinterpret_cast<char*>(base+56),"LocalPlayer")) return 2;
    auto info_xuid=read64(32);
    ctx.r3.u64=0; ctx.r4.u64=flags==2?1:2; ctx.r5.u64=96;
    __imp__XamUserGetXUID(ctx,base);
    if(ctx.r3.u32 || read64(96)!=info_xuid) return 3;
    ctx.r3.u64=info_xuid;
    __imp__XamUserGetMembershipTierFromXUID(ctx,base);
    if(ctx.r3.u32!=6) return 4;
  }
  for(uint32_t user:{0u,0xffu,1u,3u,4u}) {
    PPCContext ctx{}; ctx.r3.u64=user; ctx.r4.u64=254; ctx.r5.u64=128;
    __imp__XamUserCheckPrivilege(ctx,base);
    const bool local=user==0 || user==0xff;
    if(read32(128)!=(local?1u:0u) || ctx.r3.u32!=(local?0u:user<4?1317u:87u)) return 5;
  }
  PPCContext ctx{}; ctx.r3.u64=1; ctx.r5.u64=32;
  __imp__XamUserGetSigninInfo(ctx,base);
  if(ctx.r3.u32!=0x80070525 || read64(32)!=0 || read32(44)!=0) return 6;
  ctx={}; ctx.r3.u64=0; ctx.r4.u64=160; ctx.r5.u64=5;
  __imp__XamUserGetName(ctx,base);
  if(ctx.r3.u32 || std::strcmp(reinterpret_cast<char*>(base+160),"Loca")) return 7;
  ctx={};
  __imp__XamUserGetSigninInfo(ctx,base);
  if(ctx.r3.u32!=0x80070057) return 8;
  ctx={}; ctx.r4.u64=2; ctx.r5.u64=0xfffffffc;
  __imp__XamUserGetXUID(ctx,base);
  if(ctx.r3.u32!=0x80070057) return 9;
  ctx={}; ctx.r3.u64=0x1234;
  __imp__XamUserGetMembershipTierFromXUID(ctx,base);
  if(ctx.r3.u32!=0) return 10;
  std::puts("PASS virtual LIVE identity: cross-API state/XUID/tier/name consistency, absent users and invalid outputs");
}
