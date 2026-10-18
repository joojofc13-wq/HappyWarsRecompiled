#include <rex/ppc.h>
#include <cstdio>

REX_EXTERN(sub_830697E8);
REX_EXTERN(sub_82D1D0A0);
static unsigned calls;
static uint64_t observed;
// Test fixture only: observe the real thunk's tail-call arguments.
extern "C" REX_FUNC(sub_83069388) { ++calls; observed=ctx.r3.u64; }
extern "C" REX_FUNC(sub_82D1B380) { ++calls; observed=ctx.r5.u64; }

int main() {
  const uint64_t inputs[]={0x1000,0x100000010ull,0x10,0x7fffffff,0xffffffff};
  for (uint64_t input:inputs) {
    PPCContext ctx{};
    ctx.r3.u64=input;
    ctx.r1.u64=0x100000;
    ctx.r4.u64=0xabcdef;
    ctx.r11.u64=0x123456789abcdef0ull;
    ctx.lr=0x81234560;
    ctx.ctr.u64=0x82223344;
    calls=0;
    sub_830697E8(ctx,nullptr);
    if(calls!=1 || observed!=input-36 || ctx.r3.u64!=input-36 ||
       ctx.r1.u64!=0x100000 || ctx.r4.u64!=0xabcdef ||
       ctx.r11.u64!=0x123456789abcdef0ull || ctx.lr!=0x81234560 || ctx.ctr.u64!=0x82223344) {
      std::fputs("Original translated tail-call thunk did not preserve its ABI\n",stderr);
      return 1;
    }
  }
  for (uint64_t input:inputs) {
    PPCContext ctx{};
    ctx.r3.u64=input;
    ctx.r4.u64=0xabcdef;
    ctx.r5.u64=~input;
    ctx.lr=0x81234560;
    calls=0;
    sub_82D1D0A0(ctx,nullptr);
    if(calls!=1 || observed!=6 || ctx.r5.u64!=6 || ctx.r3.u64!=input ||
       ctx.r4.u64!=0xabcdef || ctx.lr!=0x81234560) {
      std::fputs("Original constant-argument adapter did not preserve its ABI\n",stderr);
      return 1;
    }
  }
  std::puts("10 native original-thunk cases passed; fixture destinations only");
}
