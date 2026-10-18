#include <rex/ppc.h>
#include <iostream>
extern "C" REX_FUNC(__imp__NetDll_socket);
extern "C" REX_FUNC(__imp__NetDll_connect);
extern "C" REX_FUNC(__imp__NetDll_WSAGetLastError);
extern "C" REX_FUNC(__imp__NetDll_XHttpOpen);
extern "C" REX_FUNC(__imp__NetDll_XHttpSendRequest);
int main() {
  PPCContext ctx{};
  for(auto* fn:{__imp__NetDll_socket,__imp__NetDll_connect}) {
    ctx.r3.u64=0;
    fn(ctx,nullptr);
    if(ctx.r3.u32!=0xffffffffu) return 1;
  }
  __imp__NetDll_WSAGetLastError(ctx,nullptr);
  if(ctx.r3.u32!=10050) return 2;
  for(auto* fn:{__imp__NetDll_XHttpOpen,__imp__NetDll_XHttpSendRequest}) {
    ctx.r3.u64=1;
    fn(ctx,nullptr);
    if(ctx.r3.u64!=0) return 3;
  }
  std::cout<<"PASS guest networking reports explicit offline failures\n";
}
