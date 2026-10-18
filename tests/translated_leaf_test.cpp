#include "generated/default/happywars_pch.h"
#include <array>
#include <iostream>
#include <stdexcept>
extern "C" REX_FUNC(sub_82E0AE08);
int main() {
  try {
    alignas(32) std::array<uint8_t,0x10000> memory{};
    uint8_t* base=memory.data();
    PPCContext ctx{};
    auto store32=[&](uint32_t address,uint32_t value) {
      memory[address]=value>>24; memory[address+1]=value>>16;
      memory[address+2]=value>>8; memory[address+3]=value;
    };
    store32(0x1008,0x2000); store32(0x100c,7); store32(0x1010,0); store32(0x2000,0x3000);
    constexpr uint16_t values[]={1,5,7,150,1000,1025,65535};
    for(size_t i=0;i<7;++i) {
      // The actual PPC routine assembles this resource field low-byte first.
      memory[0x3000+i*8]=values[i]&255;
      memory[0x3001+i*8]=values[i]>>8;
    }
    for(unsigned i=0;i<7;++i) {
      ctx.r3.u64=0x1000; ctx.r4.u64=values[i];
      sub_82E0AE08(ctx,base);
      if(ctx.r3.s32!=static_cast<int32_t>(i)) throw std::runtime_error("Translated lookup returned wrong index");
    }
    for(uint16_t value:{0,2,151,65534}) {
      ctx.r3.u64=0x1000; ctx.r4.u64=value;
      sub_82E0AE08(ctx,base);
      if(ctx.r3.s32!=-1) throw std::runtime_error("Translated missing-key path failed");
    }
    store32(0x100c,0);
    ctx.r3.u64=0x1000; ctx.r4.u64=7;
    sub_82E0AE08(ctx,base);
    if(ctx.r3.s32!=-1) throw std::runtime_error("Translated empty-table path failed");
    std::cout<<"PASS real PPC function 0x82E0AE08 compiled natively: 12 cases\n";
    return 0;
  } catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
