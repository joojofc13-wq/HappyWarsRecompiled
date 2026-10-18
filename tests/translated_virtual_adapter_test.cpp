#include "generated/default/happywars_pch.h"
#include <windows.h>
#include <cstdio>

REX_EXTERN(sub_8327D108);
#ifdef HAPPYWARS_TEST_VCALL4
REX_EXTERN(sub_82C3DD30);
#endif
static unsigned calls;
static uint64_t argument6,argument7;
static REX_FUNC(ObserveFixtureDestination) {
  ++calls;
  argument6=ctx.r6.u64;
  argument7=ctx.r7.u64;
}

int main() {
  // Reserve address space only. Commit three fixture pages, not 4 GiB of RAM.
  auto* base=static_cast<uint8_t*>(VirtualAlloc(nullptr,size_t{1}<<32,MEM_RESERVE,PAGE_NOACCESS));
  if(!base) return 2;
  constexpr size_t table=REX_IMAGE_BASE+REX_IMAGE_SIZE;
  if(!VirtualAlloc(base+0x1000,0x2000,MEM_COMMIT,PAGE_READWRITE) ||
     !VirtualAlloc(base+table,0x1000,MEM_COMMIT,PAGE_READWRITE)) {
    VirtualFree(base,0,MEM_RELEASE);
    return 2;
  }
  auto store32=[&](uint32_t address,uint32_t value) {
    base[address]=value>>24; base[address+1]=value>>16;
    base[address+2]=value>>8; base[address+3]=value;
  };
  store32(0x1000,0x2000);
  store32(0x2024,REX_CODE_BASE);
  *reinterpret_cast<PPCFunc**>(base+table)=ObserveFixtureDestination;
  bool ok=true;
  for(uint64_t argument:{0ull,1ull,0x100000004ull,0xffffffffffffffffull}) {
    PPCContext ctx{};
    ctx.r3.u64=0x1000; ctx.r4.u64=argument; ctx.r5.u64=argument^0x1234;
    ctx.r1.u64=0x5550; ctx.lr=0x81234560;
    calls=0;
    sub_8327D108(ctx,base);
    ok=ok && calls==1 && argument6==argument && argument7==(argument^0x1234) &&
       ctx.r3.u64==0x1000 && ctx.r4.u64==0 && ctx.r5.u64==2 &&
       ctx.r1.u64==0x5550 && ctx.lr==0x81234560 && ctx.ctr.u64==REX_CODE_BASE;
  }
#ifdef HAPPYWARS_TEST_VCALL4
  store32(0x2004,REX_CODE_BASE);
  for(uint64_t argument:{0ull,1ull,0x100000004ull,0xffffffffffffffffull}) {
    PPCContext ctx{};
    ctx.r3.u64=0x1000; ctx.r4.u64=argument; ctx.r5.u64=argument^0x1234;
    ctx.r6.u64=argument; ctx.r7.u64=argument^0x1234;
    ctx.lr=0x81234560; ctx.r1.u64=0x5550;
    calls=0;
    sub_82C3DD30(ctx,base);
    ok=ok && calls==1 && argument6==argument && argument7==(argument^0x1234) &&
       ctx.r3.u64==0x1000 && ctx.r4.u64==argument && ctx.r5.u64==(argument^0x1234) &&
       ctx.r12.u64==0x2000 && ctx.r11.u64==REX_CODE_BASE &&
       ctx.lr==0x81234560 && ctx.r1.u64==0x5550 && ctx.ctr.u64==REX_CODE_BASE;
  }
#endif
  VirtualFree(base,0,MEM_RELEASE);
  if(!ok) { std::fputs("Original virtual adapter dispatch/arguments failed\n",stderr); return 1; }
  std::puts("Original virtual-adapter cases passed with fixture destination");
}
