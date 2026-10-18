#include <rex/ppc.h>
#include <array>
#include <chrono>
#include <cstdio>
#include <cstring>
REX_EXTERN(sub_83998350);
REX_EXTERN(sub_83999390);
REX_EXTERN(__imp__sub_83998350);
REX_EXTERN(__imp__sub_83999390);

int main() {
  alignas(32) std::array<uint8_t,32768> original{}, optimized{};
  for (unsigned size:{0u,1u,3u,4u,7u,8u,15u,16u,31u,32u,63u,64u,127u,128u,511u,4096u}) {
    for (unsigned offset=0;offset<16;++offset) {
      for (unsigned value:{0u,1u,0x7Fu,0xFFu,0x1234u}) {
        original.fill(0xA5); optimized=original;
        PPCContext a{}, b{};
        a.r1.u64=32000; a.r3.u64=128+offset; a.r4.u64=value; a.r5.u64=size;
        a.r14.u64=0x12345678; b=a;
        __imp__sub_83998350(a,original.data());
        sub_83998350(b,optimized.data());
        if (original!=optimized || a.r3.u64!=b.r3.u64 || b.r14.u64!=0x12345678) return 1;
      }
      for (unsigned source_offset=0;source_offset<16;++source_offset) {
        for (size_t i=0;i<original.size();++i) original[i]=uint8_t(i*17);
        optimized=original;
        PPCContext a{}, b{};
        a.r1.u64=32000; a.r3.u64=128+offset; a.r4.u64=8192+source_offset; a.r5.u64=size;
        b=a;
        __imp__sub_83999390(a,original.data()); sub_83999390(b,optimized.data());
        // Original memcpy also saves r3 in the guest stack's volatile save area.
        if (std::memcmp(original.data(),optimized.data(),31000) || a.r3.u64!=b.r3.u64) return 2;
      }
    }
  }
  for (unsigned destination:{256u,260u}) {
    original.fill(0x5A); optimized=original;
    PPCContext a{},b{}; a.r1.u64=32000; a.r3.u64=destination; a.r4.u64=258; a.r5.u64=32; b=a;
    __imp__sub_83999390(a,original.data()); sub_83999390(b,optimized.data());
    if (original!=optimized || a.r3.u64!=b.r3.u64) return 3;
  }
  auto benchmark=[&](PPCFunc* function) {
    const auto begin=std::chrono::steady_clock::now();
    for (unsigned i=0;i<100000;++i) {
      PPCContext ctx{};ctx.r1.u64=32000;ctx.r3.u64=128;ctx.r4.u64=i;ctx.r5.u64=4096;
      function(ctx,optimized.data());
    }
    return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
  };
  const auto baseline=benchmark(__imp__sub_83998350), fast=benchmark(sub_83998350);
  std::printf("PASS original CRT comparison; 4 KiB memset microbenchmark: translated %.2f ms, native %.2f ms\n",baseline,fast);
}
