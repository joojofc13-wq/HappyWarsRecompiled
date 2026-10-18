// Load and verify an updated image without executing guest instructions.
#include <rex/runtime.h>
#include <rex/logging.h>
#include <rex/kernel/init.h>
#include <rex/system/user_module.h>
#include <rex/system/xex_module.h>
#include <fstream>
#include <iostream>
#include <string_view>

int main(int argc,char** argv) {
  const bool base_image=argc==6 && std::string_view(argv[5])=="--base-image";
  if(argc!=5 && !base_image) {std::cerr<<"Usage: title_update_probe GAME UPDATE SCRATCH OUTPUT [--base-image]\n";return 2;}
  if(!base_image && !std::filesystem::exists(std::filesystem::path(argv[1])/"Default.xexp")) {
    std::cerr<<"Sibling Default.xexp required\n";return 2;
  }
  std::filesystem::create_directories(argv[3]);
  rex::InitLogging(std::filesystem::path(argv[3])/"probe.log");
  const std::filesystem::path output=argv[4];
  if(std::filesystem::exists(output)) {std::cerr<<"Output already exists\n";return 2;}
  rex::Runtime runtime(argv[1],argv[3],argv[2]);
  auto status=runtime.Setup(rex::RuntimeConfig{
    .kernel_init=rex::kernel::InitializeKernel,.tool_mode=true});
  if(status) {std::cerr<<"Runtime setup failed\n";return 3;}
  status=runtime.LoadXexImage("game:\\Default.xex");
  if(status) {std::cerr<<"Updated image load failed\n";return 4;}
  auto module=runtime.kernel_state()->GetExecutableModule();
  if(!module || !module->xex_module()) return 5;
  const auto* image=module->xex_module();
  std::filesystem::create_directories(output);
  std::ofstream binary(output/"loaded-image.bin",std::ios::binary);
  binary.write(reinterpret_cast<const char*>(runtime.memory()->TranslateVirtual(image->base_address())),image->image_size());
  std::ofstream header(output/"patched-header.bin",std::ios::binary);
  header.write(reinterpret_cast<const char*>(image->xex_header()),image->xex_header()->header_size);
  if(!binary || !header) return 6;
  std::cout<<"Game image loaded; base="<<std::hex<<image->base_address()
           <<" entry="<<image->entry_point()<<" size="<<image->image_size()<<"\n";
  rex::FlushLogging();
}
