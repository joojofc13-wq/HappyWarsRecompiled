#include "verified_callbacks.h"
#include <rex/runtime.h>
#include <rex/ppc.h>
#include <rex/system/function_dispatcher.h>
#include <stdexcept>

// Exact native behavior of the original, verified single instruction `blr`.
// In particular, r3 and every other register are left unchanged.
extern "C" REX_FUNC(HappyWarsOriginalBlr) { (void)ctx; (void)base; }

void RegisterVerifiedCallbacks(rex::Runtime& runtime) {
  constexpr uint32_t entries[]={
#include "private/aot-callbacks/verified_blr_entries.inc"
  };
  auto* dispatcher=runtime.function_dispatcher();
  for(uint32_t address:entries) {
    if(dispatcher->GetFunction(address)) continue;
    auto* instruction=runtime.memory()->TranslateVirtual<rex::be<uint32_t>*>(address);
    if(*instruction!=0x4e800020u) throw std::runtime_error("Original blr callback differs from analyzed binary");
    if(!dispatcher->SetFunction(address,HappyWarsOriginalBlr))
      throw std::runtime_error("Original blr callback lies outside the guest module");
  }
  REXLOG_INFO("Registered {} verified original single-blr callbacks",std::size(entries));
}
