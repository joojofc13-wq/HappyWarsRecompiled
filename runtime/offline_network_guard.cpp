// Explicit failure at guest networking boundaries for offline bring-up.
// This is NOT a local server implementation and does not fabricate responses.
#include <rex/ppc.h>

namespace {
void socket_unavailable(PPCContext& ctx) { ctx.r3.u64=0xffffffffu; }
}

REX_HOOK_RAW(__imp__NetDll_socket) { (void)base; socket_unavailable(ctx); }
REX_HOOK_RAW(__imp__NetDll_connect) { (void)base; socket_unavailable(ctx); }
REX_HOOK_RAW(__imp__NetDll_send) { (void)base; socket_unavailable(ctx); }
REX_HOOK_RAW(__imp__NetDll_sendto) { (void)base; socket_unavailable(ctx); }
REX_HOOK_RAW(__imp__NetDll_accept) { (void)base; socket_unavailable(ctx); }
REX_HOOK_RAW(__imp__NetDll_WSAGetLastError) { (void)base; ctx.r3.u64=10050; } // WSAENETDOWN
