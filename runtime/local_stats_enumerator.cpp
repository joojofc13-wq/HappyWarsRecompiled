// Empty local leaderboards use real SDK handles and enumeration completion.
#include <rex/ppc.h>
#include <rex/runtime.h>
#include <rex/system/xenumerator.h>
#include <bit>
#include <cstring>
#include <vector>

namespace {
bool span(uint8_t* base,uint32_t p,uint64_t n) {
  return base && p && uint64_t(p)+n<=0x100000000ULL;
}
uint32_t read(uint8_t* base,uint32_t p) {
  uint32_t value;std::memcpy(&value,base+p,4);return std::byteswap(value);
}
void write(uint8_t* base,uint32_t p,uint32_t value) {
  value=std::byteswap(value);std::memcpy(base+p,&value,4);
}
class LocalStatsEnumerator final : public rex::system::XEnumerator {
 public:
  LocalStatsEnumerator(rex::system::KernelState* kernel,std::vector<uint32_t> views)
      :XEnumerator(kernel,1,8+16*views.size()),views_(std::move(views)) {}
  uint32_t WriteItems(uint32_t address,uint8_t* output,uint32_t* count) override {
    if(count) *count=0;
    if(done_) return 18; // ERROR_NO_MORE_FILES
    if(!output || !address || uint64_t(address)+item_size()>0x100000000ULL) return 87;
    std::memset(output,0,item_size());
    auto store=[&](size_t offset,uint32_t value) {
      value=std::byteswap(value);std::memcpy(output+offset,&value,4);
    };
    store(0,uint32_t(views_.size()));store(4,address+8);
    for(size_t i=0;i<views_.size();++i) store(8+i*16,views_[i]);
    done_=true;
    if(count) *count=1;
    return 0;
  }
 private:
  std::vector<uint32_t> views_;
  bool done_=false;
};
}

REX_HOOK_RAW(__imp__XamUserCreateStatsEnumerator) {
  const auto type=ctx.r4.u32,rows=ctx.r6.u32,views=ctx.r7.u32,specs=ctx.r8.u32;
  const auto size=ctx.r9.u32,handle=ctx.r10.u32;
  if(span(base,handle,4)) write(base,handle,0);
  if(type>3 || !ctx.r5.u64 || !rows || rows>100 || !views || views>64 ||
      !span(base,specs,uint64_t(views)*136) || !span(base,size,4) || !span(base,handle,4)) {
    ctx.r3.u64=87;return;
  }
  std::vector<uint32_t> ids;
  for(uint32_t i=0;i<views;++i) {
    if(read(base,specs+i*136+4)>64) {ctx.r3.u64=87;return;}
    ids.push_back(read(base,specs+i*136));
  }
  auto* runtime=rex::Runtime::instance();
  if(!runtime || !runtime->kernel_state()) {ctx.r3.u64=31;return;}
  auto enumerator=rex::system::object_ref<LocalStatsEnumerator>(
      new LocalStatsEnumerator(runtime->kernel_state(),std::move(ids)));
  const auto status=enumerator->Initialize(0xff,0xfb,0xb0023,0xb0024,0);
  if(status) {ctx.r3.u64=status;return;}
  write(base,size,uint32_t(enumerator->item_size()));
  write(base,handle,enumerator->handle());
  ctx.r3.u64=0;
  REXLOG_INFO("Local stats enumerator: handle={:#x}, views={}, empty ranked rows",enumerator->handle(),views);
}
