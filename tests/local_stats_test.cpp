#include <rex/ppc.h>
#include <array>
#include <bit>
#include <cstring>
#include <cstdio>
REX_EXTERN(sub_830EFE38);
REX_EXTERN(sub_82AAA650);
REX_EXTERN(sub_82AAA518);
namespace {
unsigned completions=0;
uint32_t read(uint8_t* base,uint32_t p) {
  uint32_t n;std::memcpy(&n,base+p,4);return std::byteswap(n);
}
void write(uint8_t* base,uint32_t p,uint32_t n) {
  n=std::byteswap(n);std::memcpy(base+p,&n,4);
}
}
// Test observer for the SDK's completion boundary. The real wrapper remains
// responsible for dispatch and overlapped completion in the game.
extern "C" REX_FUNC(__imp__sub_830EFE38) {
  if(read(base,ctx.r9.u32)!=ctx.r6.u32) {ctx.r3.u64=0xbad;return;}
  ++completions;ctx.r3.u64=ctx.r10.u32?997:0;
}
int main() {
  std::array<uint8_t,65536> memory{};
  auto* base=memory.data();
  for(uint32_t views:{1u,2u}) {
    write(base,256,101);write(base,260,3);
    write(base,392,202);write(base,396,2);
    write(base,128,0);
    auto call=[&](uint32_t async) {
      PPCContext ctx{};ctx.r4.u64=1;ctx.r6.u64=views;ctx.r7.u64=256;
      ctx.r8.u64=128;ctx.r9.u64=2048;ctx.r10.u64=async;
      sub_830EFE38(ctx,base);return ctx.r3.u32;
    };
    if(call(0)!=122) return 1;
    const auto required=read(base,128);
    if(required!=8+(16+52)*views+(views==1?3:5)*28) return 2;
    if(call(1)!=997 || read(base,2048)!=views || read(base,2052)!=2056 ||
        read(base,2056)!=101 || read(base,2064)) return 3;
    if(views==2 && read(base,2072)!=202) return 4;
    // Run both original consumers against the local result. An empty result
    // previously left views_ptr null and faulted when they read views_ptr+4.
    for(auto consumer:{sub_82AAA650,sub_82AAA518}) {
      write(base,4096,2048);write(base,4104,0xdeadbeef);write(base,4108,0xdeadbeef);
      PPCContext ctx{};ctx.r1.u64=60000;ctx.r4.u64=4096;ctx.lr=0x12345678;
      ctx.r29.u64=11;ctx.r30.u64=22;ctx.r31.u64=33;
      consumer(ctx,base);
      if(read(base,4104) || read(base,4108) || ctx.lr!=0x12345678 ||
          ctx.r29.u64!=11 || ctx.r30.u64!=22 || ctx.r31.u64!=33) return 5;
    }
  }
  if(completions!=2) return 6;
  std::puts("PASS local stats sizing and views; both original translated consumers accept empty rows");
}
