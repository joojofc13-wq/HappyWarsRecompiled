#include <rex/ppc.h>
#include <rex/runtime.h>
#include <rex/kernel/init.h>
#include <bit>
#include <chrono>
#include <cstring>
#include <cstdio>
REX_EXTERN(__imp__XamUserCreateStatsEnumerator);
REX_EXTERN(__imp__XamEnumerate);
REX_EXTERN(__imp__NtClose);
int main(int argc,char** argv) {
  if(argc!=2) return 1;
  const auto scratch=std::filesystem::path(argv[1]).concat("."+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
  rex::Runtime runtime({},scratch);
  if(runtime.Setup(rex::RuntimeConfig{.kernel_init=rex::kernel::InitializeKernel,.tool_mode=true})) return 2;
  auto* base=runtime.memory()->virtual_membase();
  const auto block=runtime.memory()->SystemHeapAlloc(4096);
  auto write=[&](uint32_t p,uint32_t v){v=std::byteswap(v);std::memcpy(base+p,&v,4);};
  auto read=[&](uint32_t p){uint32_t v;std::memcpy(&v,base+p,4);return std::byteswap(v);};
  write(block,101);write(block+4,2);write(block+136,202);write(block+140,1);
  PPCContext ctx{};
  ctx.r3.u64=0x58410ae9;ctx.r4.u64=1;ctx.r5.u64=1;ctx.r6.u64=10;
  ctx.r7.u64=2;ctx.r8.u64=block;ctx.r9.u64=block+512;ctx.r10.u64=block+516;
  __imp__XamUserCreateStatsEnumerator(ctx,base);
  if(ctx.r3.u32 || read(block+512)!=40 || !read(block+516)) return 3;
  const auto handle=read(block+516),buffer=block+1024,count=block+520;
  auto enumerate=[&]{
    ctx={};ctx.r3.u64=handle;ctx.r5.u64=buffer;ctx.r6.u64=40;ctx.r7.u64=count;
    __imp__XamEnumerate(ctx,base);return ctx.r3.u32;
  };
  if(enumerate() || read(count)!=1 || read(buffer)!=2 || read(buffer+4)!=buffer+8 ||
      read(buffer+8)!=101 || read(buffer+24)!=202 || read(buffer+12) || read(buffer+20)) return 4;
  if(enumerate()!=18 || read(count)) return 5;
  ctx={};ctx.r3.u64=handle;__imp__NtClose(ctx,base);
  if(ctx.r3.u32 || enumerate()!=6) return 6;
  runtime.memory()->SystemHeapFree(block);
  std::puts("PASS real SDK stats handle: empty views, enumeration completion, EOF and close");
}
