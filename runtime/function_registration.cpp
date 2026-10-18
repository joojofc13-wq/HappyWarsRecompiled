#include <rex/ppc/func.h>
#include <rex/system/function_dispatcher.h>

// Same order, addresses and native pointers as the SDK-generated registration.
// scripts/verify_registration.py checks both original lists before every build.
void happywars_RegisterFunctions(rex::runtime::IModuleRegistrar* registrar) {
  for (const auto* mapping=PPCFuncMappings; mapping->host; ++mapping)
    registrar->SetFunction(static_cast<uint32_t>(mapping->guest),mapping->host);
}
