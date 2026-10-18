#include <rex/ppc.h>
#include <array>
#include <bit>
#include <cstring>
#include <cstdio>
REX_EXTERN(__imp__XampXAuthStartup);
REX_EXTERN(__imp__XampXAuthShutdown);
REX_EXTERN(__imp__XampXAuthGetTitleBuffer);
int main() {
  std::array<uint8_t,64> memory{};
  auto* base=memory.data();
  PPCContext ctx{};
  for(uint32_t size:{8u,0u,4u,12u}) {
    auto encoded=std::byteswap(size);
    std::memcpy(base+16,&encoded,4);
    ctx.r3.u64=16;
    __imp__XampXAuthStartup(ctx,base);
    if(ctx.r3.u32!=(size==8?0u:0x80158401u)) return 1;
  }
  ctx.r3.u64=32;
  __imp__XampXAuthShutdown(ctx,base);
  if(memory[35]!=1 || memory[32]!=0) return 2;
  for(uint64_t stale:{0ULL,32ULL,0xdeadbeefULL}) {
    ctx.r3.u64=stale;
    __imp__XampXAuthGetTitleBuffer(ctx,base);
    if(ctx.r3.u64) return 3;
  }
  std::puts("PASS XAuth structure validation, shutdown completion and explicit absent buffer");
}
