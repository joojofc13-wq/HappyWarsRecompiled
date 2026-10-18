#include <rex/codegen/function_graph.h>
#include <random>
#include <iostream>
using namespace rex::codegen;
int main() {
  FunctionGraph graph;
  std::mt19937 random(81244);
  uint64_t hash=1469598103934665603ULL;
  auto add=[&](uint64_t value) { hash=(hash^value)*1099511628211ULL; };
  for(unsigned event=0;event<20000;++event) {
    uint32_t entry=0x82000000+(random()%300)*256;
    uint32_t target=0x82000000+(random()%400)*256;
    switch(random()%5) {
      case 0: graph.addFunction(entry,128,static_cast<FunctionAuthority>(random()%7)); break;
      case 1: graph.addFunction(target,128,FunctionAuthority::DISCOVERED); break;
      case 2: graph.removeFunction(entry); break;
      default: graph.addUnresolvedJumpToFunction(entry,entry+4*(random()%32),target,
                                                random()%2,random()%2); break;
    }
    // Compare complete unresolved lists and the ordered call-site lists after
    // each operation, including node replacement and stale waiter situations.
    for(uint32_t address=0x82000000;address<0x82000000+400*256;address+=256) {
      auto* node=graph.getFunction(address);
      if(!node) continue;
      add(address); add(node->unresolvedJumps().size());
      for(const auto& jump:node->unresolvedJumps()) {
        add(jump.site); add(jump.target); add(jump.isCall); add(jump.isConditional);
      }
      add(node->calls().size()); add(node->tailCalls().size());
      for(const auto& call:node->calls()) add(call.site);
      for(const auto& call:node->tailCalls()) add(call.site);
    }
  }
  std::cout<<hash<<"\n";
}
