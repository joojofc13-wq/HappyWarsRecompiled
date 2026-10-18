#include "generated/default/happywars_pch.h"
#include <windows.h>
#include <cstdio>

REX_EXTERN(sub_82B67950);
static unsigned calls;
static unsigned selected;
static REX_FUNC(ObserveZero) { ++calls; selected=0; }
static REX_FUNC(ObserveOne) { ++calls; selected=1; }

int main() {
  auto* base=static_cast<uint8_t*>(VirtualAlloc(nullptr,size_t{1}<<32,MEM_RESERVE,PAGE_NOACCESS));
  if(!base) return 2;
  constexpr uint32_t targets[]={0x82B67940,0x82B67930};
  constexpr size_t dispatch=REX_IMAGE_BASE+REX_IMAGE_SIZE+(targets[1]-REX_CODE_BASE)*2;
  const size_t pages[]={0x1000,0x820ba000,dispatch&~size_t{0xfff}};
  for(size_t page:pages) {
    if(!VirtualAlloc(base+page,0x1000,MEM_COMMIT,PAGE_READWRITE)) {
      VirtualFree(base,0,MEM_RELEASE); return 2;
    }
  }
  auto store32=[&](uint32_t address,uint32_t value) {
    base[address]=value>>24; base[address+1]=value>>16;
    base[address+2]=value>>8; base[address+3]=value;
  };
  store32(0x820baf2c,targets[0]); store32(0x820baf30,targets[1]);
  for(unsigned i=0;i<2;++i) {
    size_t slot=REX_IMAGE_BASE+REX_IMAGE_SIZE+(targets[i]-REX_CODE_BASE)*2;
    *reinterpret_cast<PPCFunc**>(base+slot)=i==0?ObserveZero:ObserveOne;
  }
  bool ok=true;
  for(unsigned index:{0u,1u,1u,0u}) {
    PPCContext ctx{};
    store32(0x1004,index);
    ctx.r3.u64=0x1000; ctx.r4.u64=0x123456789abcdef0ull;
    ctx.lr=0x81234560; ctx.r1.u64=0x5550;
    calls=0; selected=99;
    sub_82B67950(ctx,base);
    ok=ok && calls==1 && selected==index && ctx.ctr.u64==targets[index] &&
       ctx.r10.u32==0x820baf2c && ctx.r11.u64==targets[index] &&
       ctx.r3.u64==0x1000 && ctx.r4.u64==0x123456789abcdef0ull &&
       ctx.lr==0x81234560 && ctx.r1.u64==0x5550;
  }
  VirtualFree(base,0,MEM_RELEASE);
  if(!ok) { std::fputs("Original indexed dispatch selected wrong callback or changed ABI\n",stderr); return 1; }
  std::puts("4 original indexed-dispatch cases passed with fixture callbacks");
}
