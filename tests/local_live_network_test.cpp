#include <rex/ppc.h>
#include <array>
#include <cstdio>
REX_EXTERN(__imp__NetDll_XNetGetTitleXnAddr);
int main() {
  std::array<uint8_t,4096> memory;
  memory.fill(0xa5);
  PPCContext ctx{};ctx.r3.u64=1;ctx.r4.u64=256;
  __imp__NetDll_XNetGetTitleXnAddr(ctx,memory.data());
  if(ctx.r3.u32!=0x86 || !(ctx.r3.u32&0x80) || memory[256]!=127 || memory[259]!=1 ||
      memory[260]!=127 || memory[263]!=1 || memory[266]!=2 ||
      memory[255]!=0xa5 || memory[292]!=0xa5) return 1;
  ctx={};__imp__NetDll_XNetGetTitleXnAddr(ctx,memory.data());
  if(ctx.r3.u32!=1) return 2;
  std::puts("PASS local XNADDR: ready online flag, loopback addresses and bounded output");
}
