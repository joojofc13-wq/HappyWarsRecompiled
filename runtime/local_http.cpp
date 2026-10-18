// In-process XHTTP transport. No DNS, sockets or remote HTTP client is used.
#include "local_http.h"
#include "local_title_storage.h"
#include <rex/ppc.h>
#include <algorithm>
#include <bit>
#include <cstring>
#include <deque>
#include <memory>
#include <mutex>
#include <unordered_map>

namespace {
enum class Kind { Session, Connection, Request };
struct Handle {
  Kind kind;
  uint32_t callback=0,context=0,mask=0;
  std::string host,method,path;
  std::vector<uint8_t> upload;
  happywars::LocalResponse response{0,"",{}};
  size_t position=0;
};
struct Event { uint32_t handle,callback,context,status,info,length; };
std::mutex mutex;
std::unordered_map<uint32_t,Handle> handles;
std::deque<Event> events;
uint32_t next_handle=0x71000000;
std::unique_ptr<happywars::LocalTitleStorage> service;
bool valid(uint8_t* base,uint32_t address,uint32_t size) {
  return base && address && uint64_t(address)+size<=0x100000000ULL;
}
uint32_t read32(uint8_t* base,uint32_t address) {
  uint32_t n; std::memcpy(&n,base+address,4); return std::byteswap(n);
}
void write32(uint8_t* base,uint32_t address,uint32_t n) {
  n=std::byteswap(n); std::memcpy(base+address,&n,4);
}
std::string string(uint8_t* base,uint32_t address) {
  if(!address || !base) return {};
  std::string result;
  for(uint32_t i=0;i<4096 && uint64_t(address)+i<0x100000000ULL;i++) {
    const auto c=base[address+i];
    if(!c) return result;
    result+=char(c);
  }
  return {};
}
uint32_t add(Handle value) {
  const auto id=++next_handle;
  handles.emplace(id,std::move(value));
  return id;
}
void queue(uint32_t id,Handle& h,uint32_t status,uint32_t info=0,uint32_t length=0) {
  if(h.callback && (h.mask&status)) events.push_back({id,h.callback,h.context,status,info,length});
}
}

void InitializeLocalHttp(const std::filesystem::path& database) {
  std::scoped_lock lock(mutex);
  service=std::make_unique<happywars::LocalTitleStorage>(database);
}

REX_HOOK_RAW(__imp__NetDll_XHttpStartup) { ctx.r3.u64=1; }
REX_HOOK_RAW(__imp__NetDll_XHttpShutdown) {
  std::scoped_lock lock(mutex); handles.clear(); events.clear(); service.reset(); ctx.r3.u64=0;
}
REX_HOOK_RAW(__imp__NetDll_XHttpOpen) {
  std::scoped_lock lock(mutex);
  ctx.r3.u64=add(Handle{Kind::Session});
  REXLOG_INFO("Local HTTP: opened session {:#x}",ctx.r3.u32);
}
REX_HOOK_RAW(__imp__NetDll_XHttpConnect) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end() || found->second.kind!=Kind::Session) { ctx.r3.u64=0; return; }
  auto h=found->second; h.kind=Kind::Connection; h.host=string(base,ctx.r5.u32);
  REXLOG_INFO("Local HTTP: connection for host '{}' stays in process",h.host);
  ctx.r3.u64=add(std::move(h));
}
REX_HOOK_RAW(__imp__NetDll_XHttpOpenRequest) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end() || found->second.kind!=Kind::Connection) { ctx.r3.u64=0; return; }
  auto h=found->second; h.kind=Kind::Request;
  h.method=string(base,ctx.r5.u32); h.path=string(base,ctx.r6.u32);
  if(h.method.empty()) h.method="GET";
  REXLOG_INFO("Local HTTP: request {} {}",h.method,h.path.substr(0,h.path.find('?')));
  ctx.r3.u64=add(std::move(h));
}
REX_HOOK_RAW(__imp__NetDll_XHttpSetStatusCallback) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end()) { ctx.r3.u64=0xffffffff; return; }
  const auto previous=found->second.callback;
  found->second.callback=ctx.r5.u32;
  found->second.mask=ctx.r6.u32;
  ctx.r3.u64=previous;
}
REX_HOOK_RAW(__imp__NetDll_XHttpCloseHandle) {
  std::scoped_lock lock(mutex);
  const auto id=ctx.r4.u32;
  ctx.r3.u64=handles.erase(id)?1:0;
  std::erase_if(events,[&](const auto& e){return e.handle==id;});
}
REX_HOOK_RAW(__imp__NetDll_XHttpSendRequest) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end() || found->second.kind!=Kind::Request || ctx.r8.u32>64*1024*1024 ||
     (ctx.r8.u32 && !valid(base,ctx.r7.u32,ctx.r8.u32))) { ctx.r3.u64=0; return; }
  auto& h=found->second;
  h.context=ctx.r10.u32; h.position=0; h.upload.clear();
  if(ctx.r8.u32) h.upload.assign(base+ctx.r7.u32,base+ctx.r7.u32+ctx.r8.u32);
  queue(found->first,h,0x400000,ctx.r7.u32,ctx.r8.u32);
  ctx.r3.u64=1;
}
REX_HOOK_RAW(__imp__NetDll_XHttpWriteData) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end() || found->second.kind!=Kind::Request || !valid(base,ctx.r5.u32,ctx.r6.u32) ||
      found->second.upload.size()+ctx.r6.u32>64*1024*1024) { ctx.r3.u64=0; return; }
  auto& h=found->second;
  h.upload.insert(h.upload.end(),base+ctx.r5.u32,base+ctx.r5.u32+ctx.r6.u32);
  if(valid(base,ctx.r7.u32,4)) write32(base,ctx.r7.u32,ctx.r6.u32);
  queue(found->first,h,0x100000,ctx.r7.u32,4);
  ctx.r3.u64=1;
}
REX_HOOK_RAW(__imp__NetDll_XHttpReceiveResponse) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end() || found->second.kind!=Kind::Request || !service) { ctx.r3.u64=0; return; }
  auto& h=found->second;
  try { h.response=service->request(h.method,h.path,h.upload); }
  catch(const std::exception& error) {
    REXLOG_ERROR("Local HTTP storage failure: {}",error.what());
    h.response={500,"application/json",{}};
  }
  REXLOG_INFO("Local HTTP: {} {} -> {} ({} bytes)",h.method,h.path.substr(0,h.path.find('?')),h.response.status,h.response.body.size());
  queue(found->first,h,0x20000);
  ctx.r3.u64=1;
}
REX_HOOK_RAW(__imp__NetDll_XHttpQueryHeaders) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  const auto output=ctx.r7.u32,size_ptr=ctx.r8.u32,query=ctx.r5.u32;
  if(found==handles.end() || found->second.kind!=Kind::Request || !valid(base,size_ptr,4)) { ctx.r3.u64=0; return; }
  const auto& response=found->second.response;
  uint32_t number=0;
  std::string value;
  switch(query&0xffff) {
    case 0xfffe: number=response.status; value=std::to_string(number); break;
    case 9: number=uint32_t(response.body.size()); value=std::to_string(number); break;
    case 0xffff:
      if(string(base,ctx.r6.u32)!="ETag") { ctx.r3.u64=0; return; }
      value="\"local\""; break;
    case 1: value=response.content_type; break;
    case 22: value="HTTP/1.1 "+std::to_string(response.status)+"\r\nContent-Length: "+std::to_string(response.body.size())+"\r\nContent-Type: "+response.content_type+"\r\n\r\n"; break;
    default: ctx.r3.u64=0; return;
  }
  const uint32_t needed=(query&0x20000000)?4:uint32_t(value.size()+1);
  const auto capacity=read32(base,size_ptr);
  write32(base,size_ptr,needed);
  if(capacity<needed || !valid(base,output,needed)) { ctx.r3.u64=0; return; }
  if(query&0x20000000) write32(base,output,number);
  else std::memcpy(base+output,value.c_str(),needed);
  ctx.r3.u64=1;
}
REX_HOOK_RAW(__imp__NetDll_XHttpReadData) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end() || found->second.kind!=Kind::Request || !valid(base,ctx.r5.u32,ctx.r6.u32)) { ctx.r3.u64=0; return; }
  auto& h=found->second;
  const auto count=uint32_t(std::min(size_t(ctx.r6.u32),h.response.body.size()-h.position));
  if(count) std::memcpy(base+ctx.r5.u32,h.response.body.data()+h.position,count);
  h.position+=count;
  if(valid(base,ctx.r7.u32,4)) write32(base,ctx.r7.u32,count);
  queue(found->first,h,0x80000,ctx.r5.u32,count);
  ctx.r3.u64=1;
}
REX_HOOK_RAW(__imp__NetDll_XHttpSetOption) {
  std::scoped_lock lock(mutex);
  const auto found=handles.find(ctx.r4.u32);
  if(found==handles.end()) { ctx.r3.u64=0; return; }
  if(ctx.r5.u32==45) {
    if(ctx.r7.u32<4 || !valid(base,ctx.r6.u32,4)) { ctx.r3.u64=0; return; }
    found->second.context=read32(base,ctx.r6.u32);
  }
  ctx.r3.u64=1; // Timeouts/security transport flags have no external transport here.
}
REX_HOOK_RAW(__imp__NetDll_XHttpDoWork) {
  std::deque<Event> ready;
  { std::scoped_lock lock(mutex); ready.swap(events); }
  for(const auto& event:ready) {
    { std::scoped_lock lock(mutex);
      const auto found=handles.find(event.handle);
      if(found==handles.end() || found->second.callback!=event.callback) continue;
    }
    rex::CallFrame frame(ctx);
    frame.ctx.r1.u32-=0x100;
    frame.ctx.r3.u64=event.handle; frame.ctx.r4.u64=event.context;
    frame.ctx.r5.u64=event.status; frame.ctx.r6.u64=event.info; frame.ctx.r7.u64=event.length;
    rex::runtime::ResolveIndirectFunction(event.callback)(frame.ctx,base);
  }
  ctx.r3.u64=1;
}
