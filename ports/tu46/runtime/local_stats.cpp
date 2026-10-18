// Preserve the original stats wrapper and its completion handling, but provide
// well-formed empty local views before the SDK reports the request complete.
#include <rex/ppc.h>
#include <bit>
#include <cstring>
REX_EXTERN(__imp__sub_83793270);
namespace {
bool valid(uint8_t* base,uint32_t p,uint64_t length) {
  return base && p && uint64_t(p)+length<=0x100000000ULL;
}
uint32_t read(uint8_t* base,uint32_t p) {
  uint32_t n;std::memcpy(&n,base+p,4);return std::byteswap(n);
}
void write(uint8_t* base,uint32_t p,uint32_t n) {
  n=std::byteswap(n);std::memcpy(base+p,&n,4);
}
}
REX_HOOK_RAW(sub_83793270) {
  const auto users=ctx.r4.u32,views=ctx.r6.u32,specs=ctx.r7.u32;
  const auto size_ptr=ctx.r8.u32,output=ctx.r9.u32;
  if(!users || users>100 || !views || views>64 || !valid(base,specs,uint64_t(views)*136) ||
      !valid(base,size_ptr,4)) { ctx.r3.u64=87;return; }
  // Same required-size formula as the original wrapper, including row/column
  // reserve space even though this local leaderboard has no rows.
  uint64_t required=8+uint64_t(16+52*users)*views;
  for(uint32_t i=0;i<views;i++) {
    const auto columns=read(base,specs+i*136+4);
    if(columns>64) { ctx.r3.u64=87;return; }
    required+=uint64_t(columns)*users*28;
  }
  const auto capacity=read(base,size_ptr);
  if(required>capacity) {
    write(base,size_ptr,uint32_t(required));ctx.r3.u64=122;return;
  }
  const uint32_t empty_size=8+16*views;
  if(!valid(base,output,empty_size)) { ctx.r3.u64=87;return; }
  std::memset(base+output,0,empty_size);
  write(base,output,views);
  write(base,output+4,output+8);
  for(uint32_t i=0;i<views;i++) write(base,output+8+i*16,read(base,specs+i*136));
  REXLOG_INFO("Local stats: {} requested views initialized with zero rows",views);
  __imp__sub_83793270(ctx,base);
}
