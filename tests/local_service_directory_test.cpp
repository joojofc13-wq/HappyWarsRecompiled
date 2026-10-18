#include <rex/ppc.h>
#include <array>
#include <cstring>
#include <cstdio>
REX_EXTERN(sub_832C0900);
int main() {
  std::array<uint8_t,256> memory{};
  std::memcpy(memory.data()+16,"services",9);
  auto call=[&](uint32_t capacity,uint32_t async=0) {
    PPCContext ctx{}; ctx.r3.u64=16; ctx.r4.u64=64; ctx.r5.u64=capacity; ctx.r6.u64=async;
    sub_832C0900(ctx,memory.data()); return ctx.r3.u32;
  };
  if(call(8)!=122 || memory[64]) return 1;
  if(call(128) || std::strcmp(reinterpret_cast<char*>(memory.data()+64),"http://happywars.local:80")) return 2;
  if(call(128,1)!=50) return 3;
  memory[16]='x'; if(call(128)!=1168) return 4;
  PPCContext ctx{}; sub_832C0900(ctx,memory.data());
  if(ctx.r3.u32!=87) return 5;
  std::puts("PASS actual service lookup ABI, capacity, unknown service and asynchronous rejection");
}
