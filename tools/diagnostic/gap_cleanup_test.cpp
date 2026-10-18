#include "gap_cleanup.h"
#include <random>
#include <stdexcept>
#include <iostream>
using namespace rex::codegen;
std::vector<uint32_t> reference(const FunctionGraph& graph) {
  std::vector<uint32_t> result;
  for(const auto& [address,node]:graph.functions()) {
    if(node->authority()!=FunctionAuthority::GAP_FILL) continue;
    for(const auto& [otherAddress,other]:graph.functions()) {
      if(otherAddress==address || !other->containsAddress(address)) continue;
      if(other->authority()!=FunctionAuthority::GAP_FILL || otherAddress<address) {
        result.push_back(address); break;
      }
    }
  }
  std::sort(result.begin(),result.end()); return result;
}
int main() {
  std::mt19937 random(684943);
  for(unsigned trial=0;trial<300;++trial) {
    FunctionGraph graph;
    for(unsigned i=0;i<400;++i) {
      uint32_t base=0x82000000+(random()%4096)*4;
      uint32_t size=(random()%200)*4;
      auto authority=static_cast<FunctionAuthority>(random()%7);
      auto* n=graph.addFunction(base,size,authority);
      if(i%3==0 && size>16 && n->canDiscover() && !n->isImport())
        n->discover({{base+8,size-16}},{},{});
    }
    if(reference(graph)!=FindAbsorbedGapFills(graph))
      throw std::runtime_error("Cleanup differs from original query");
  }
  std::cout<<"PASS 300 graphs with overlaps, block gaps, zero sizes and mixed authorities\n";
}
