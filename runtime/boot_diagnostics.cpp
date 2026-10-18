// Non-invasive tracing of original title checks; no results are changed here.
#include <rex/ppc.h>
#include <atomic>
#include "crash_diagnostics.h"
#include <rex/system/thread_state.h>
#include <cstdio>
#include <windows.h>

namespace {
HANDLE fault_log=INVALID_HANDLE_VALUE;
LONG CALLBACK trace_null_access(EXCEPTION_POINTERS* exception) {
  const auto* record=exception->ExceptionRecord;
  if(record->ExceptionCode!=EXCEPTION_ACCESS_VIOLATION ||
      record->NumberParameters<2 || fault_log==INVALID_HANDLE_VALUE) return EXCEPTION_CONTINUE_SEARCH;
  auto* thread=rex::runtime::ThreadState::Get();
  if(!thread) return EXCEPTION_CONTINUE_SEARCH;
  const auto arena=reinterpret_cast<uintptr_t>(thread->memory()->virtual_membase());
  const auto address=record->ExceptionInformation[1];
  // Record only null-range guest faults, not normal GPU/MMIO protection events.
  if(address<arena || address-arena>=0x10000) return EXCEPTION_CONTINUE_SEARCH;
  DWORD64 image=0;
  const auto rip=exception->ContextRecord->Rip;
  const auto unwind=RtlLookupFunctionEntry(rip,&image,nullptr);
  const auto native_start=unwind?image+unwind->BeginAddress:0;
  uint32_t guest=0;
  for(const auto* mapping=PPCFuncMappings;mapping->host;++mapping)
    if(reinterpret_cast<uintptr_t>(mapping->host)==native_start) {
      guest=static_cast<uint32_t>(mapping->guest);break;
    }
  const auto* ctx=thread->context();
  char output[1024];
  const int size=std::snprintf(output,sizeof(output),
    "Guest null access: thread=%08x address=%08x operation=%llu\n"
    "native_rip=%016llx native_function=%016llx guest_function=%08x\n"
    "lr=%08x ctr=%08x sp=%08x r3=%08x r4=%08x r5=%08x r6=%08x\n"
    "r7=%08x r8=%08x r9=%08x r10=%08x r11=%08x r12=%08x\n"
    "r28=%08x r29=%08x r30=%08x r31=%08x\n",
    thread->thread_id(),uint32_t(address-arena),
    static_cast<unsigned long long>(record->ExceptionInformation[0]),
    static_cast<unsigned long long>(rip),static_cast<unsigned long long>(native_start),guest,
    uint32_t(ctx->lr),ctx->ctr.u32,ctx->r1.u32,ctx->r3.u32,ctx->r4.u32,ctx->r5.u32,ctx->r6.u32,
    ctx->r7.u32,ctx->r8.u32,ctx->r9.u32,ctx->r10.u32,ctx->r11.u32,ctx->r12.u32,
    ctx->r28.u32,ctx->r29.u32,ctx->r30.u32,ctx->r31.u32);
  DWORD written=0;
  if(size>0) WriteFile(fault_log,output,static_cast<DWORD>(std::min(size,int(sizeof(output)-1))),&written,nullptr);
  FlushFileBuffers(fault_log);
  return EXCEPTION_CONTINUE_SEARCH;
}
}

void InitializeCrashDiagnostics(const std::filesystem::path& file) {
  if(fault_log!=INVALID_HANDLE_VALUE) return;
  fault_log=CreateFileW(file.c_str(),FILE_APPEND_DATA,FILE_SHARE_READ,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(fault_log!=INVALID_HANDLE_VALUE) AddVectoredExceptionHandler(1,trace_null_access);
}

REX_EXTERN(__imp__sub_82C16438);
REX_EXTERN(__imp__sub_82C1FC18);

REX_HOOK_RAW(sub_82C16438) {
  const auto flags=ctx.r3.u32;
  const auto user=ctx.r4.u32;
  __imp__sub_82C16438(ctx,base);
  static std::atomic<unsigned> calls{};
  if(calls.fetch_add(1)<16)
    REXLOG_INFO("Title profile check: flags={:#x}, user={}, restriction={:#x}",flags,user,ctx.r3.u32);
}

REX_HOOK_RAW(sub_82C1FC18) {
  REXLOG_INFO("Title message: caller={:#x}, descriptor={:#x}, user={}, text={:#x}",
              uint32_t(ctx.lr),ctx.r3.u32,ctx.r4.u32,ctx.r5.u32);
  __imp__sub_82C1FC18(ctx,base);
}
