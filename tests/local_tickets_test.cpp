#include <rex/ppc.h>
#include <windows.h>
#include <bit>
#include <cstdio>
#include <cstring>
#include <limits>
REX_EXTERN(sub_830A1310);
REX_EXTERN(sub_830A1378);
int main() {
  auto* base=static_cast<uint8_t*>(VirtualAlloc(nullptr,0x100000000ULL,MEM_RESERVE,PAGE_NOACCESS));
  if(!base) return 99;
  struct Release { void* memory;~Release(){VirtualFree(memory,0,MEM_RELEASE);} } release{base};
  for(const uint32_t page:{0x850d1000u,0x84762000u,0x10002000u,0x10013000u})
    if(!VirtualAlloc(base+page,0x1000,MEM_COMMIT,PAGE_READWRITE)) return 98;
  auto write=[&](uint32_t address,uint32_t value) {
    value=std::byteswap(value);std::memcpy(base+address,&value,4);
  };
  PPCContext ctx{};
  sub_830A1310(ctx,base);if(ctx.r3.u32) return 1;
  base[0x850d1374]=1;
  write(0x84762e98,0x10000000);
  constexpr uint32_t save=0x10000010;
  write(save+0x2218,500);write(save+0x2210,10);
  sub_830A1310(ctx,base);if(ctx.r3.u32!=1) return 2;
  ctx.r4.u64=0x123456789abcdef0ULL;
  sub_830A1378(ctx,base);
  if(ctx.r3.u32!=490 || ctx.r4.u64!=0x123456789abcdef0ULL) return 3;
  write(save+0x2210,600);sub_830A1378(ctx,base);if(ctx.r3.u32) return 4;
  write(save+0x2210,0);
  write(save+0x2218,std::numeric_limits<int32_t>::max());
  write(save+0x136c8,std::numeric_limits<int32_t>::max());
  sub_830A1378(ctx,base);if(ctx.r3.u32!=std::numeric_limits<int32_t>::max()) return 5;
  write(0x850d1370,4);sub_830A1310(ctx,base);if(ctx.r3.u32) return 6;
  write(0x850d1370,0);write(0x84762e98,0);sub_830A1310(ctx,base);if(ctx.r3.u32) return 7;
  std::puts("PASS TU46 local ticket readiness, live save counters, spending and invalid users");
}
