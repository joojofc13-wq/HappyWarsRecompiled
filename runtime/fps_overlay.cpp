#include "fps_overlay.h"
#include <rex/ppc.h>
#include <imgui.h>
#include <windows.h>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <stdexcept>

namespace {
PPCFunc* original_swap=nullptr;
std::atomic<uint64_t> submitted_frames{};
std::atomic<uint64_t> swap_nanoseconds{};
using Clock=std::chrono::steady_clock;
class FpsOverlay final : public rex::ui::ImGuiDialog {
 public:
  FpsOverlay(rex::ui::ImGuiDrawer* drawer,ImFont* font)
      :ImGuiDialog(drawer),font_(font),sample_time_(Clock::now()),log_time_(sample_time_),
       previous_frames_(submitted_frames.load()),previous_work_(swap_nanoseconds.load()) {}
 protected:
  void OnDraw(ImGuiIO& io) override {
    const auto now=Clock::now();
    const auto elapsed=std::chrono::duration<double>(now-sample_time_).count();
    if(elapsed>=0.5) {
      const auto frames=submitted_frames.load(std::memory_order_relaxed);
      const auto work=swap_nanoseconds.load(std::memory_order_relaxed);
      const auto count=frames-previous_frames_;
      fps_=double(count)/elapsed;
      swap_ms_=count?double(work-previous_work_)/double(count)/1000000.0:0;
      previous_frames_=frames;previous_work_=work;sample_time_=now;
      if(now-log_time_>=std::chrono::seconds(5)) {
        REXLOG_INFO("Game frame rate: {:.1f} FPS; VdSwap CPU {:.3f} ms/frame; submitted {}",fps_,swap_ms_,frames);
        log_time_=now;
      }
    }
    char label[32];
    std::snprintf(label,sizeof(label),"%.0f FPS",fps_);
    constexpr float size=28;
    const auto width=font_->CalcTextSizeA(size,10000,0,label).x;
    const ImVec2 position(std::round((io.DisplaySize.x-width)*0.5f),12);
    auto* draw=ImGui::GetForegroundDrawList();
    for(const ImVec2 offset:{ImVec2(-2,0),ImVec2(2,0),ImVec2(0,-2),ImVec2(0,2)})
      draw->AddText(font_,size,ImVec2(position.x+offset.x,position.y+offset.y),IM_COL32(0,0,0,230),label);
    draw->AddText(font_,size,position,IM_COL32(255,245,222,255),label);
  }
 private:
  ImFont* font_;
  Clock::time_point sample_time_,log_time_;
  uint64_t previous_frames_,previous_work_;
  double fps_=0,swap_ms_=0;
};
}

void InitializeFrameCounter() {
  // Call the SDK's actual raw export rather than recursively resolving our hook.
  const auto module=GetModuleHandleW(L"rexruntime.dll");
  original_swap=module?reinterpret_cast<PPCFunc*>(GetProcAddress(module,"__imp__VdSwap")):nullptr;
  if(!original_swap) throw std::runtime_error("Original VdSwap export is unavailable");
}
REX_HOOK_RAW(__imp__VdSwap) {
  const auto begin=Clock::now();
  original_swap(ctx,base);
  const auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-begin).count();
  swap_nanoseconds.fetch_add(uint64_t(elapsed),std::memory_order_relaxed);
  submitted_frames.fetch_add(1,std::memory_order_relaxed);
}

ImFont* LoadGameFpsFont(ImFontAtlas* atlas) {
  wchar_t executable[32768];
  const auto length=GetModuleFileNameW(nullptr,executable,32768);
  if(!length || length==32768) throw std::runtime_error("Cannot locate FPS font directory");
  const auto file=std::filesystem::path(executable).parent_path()/"fonts/happywars-fps.ttf";
  if(!std::filesystem::exists(file)) {
    ImFontConfig config{};
    config.SizePixels=28;
    REXLOG_INFO("FPS overlay uses the built-in font; original game font was not supplied");
    return atlas->AddFontDefault(&config);
  }
  const auto path=file.u8string();
  ImFontConfig config{};
  config.OversampleH=2;config.OversampleV=2;
  static const ImWchar ranges[]={32,32,46,46,48,57,70,70,80,80,83,83,0};
  auto* font=atlas->AddFontFromFileTTF(reinterpret_cast<const char*>(path.c_str()),28,&config,ranges);
  if(!font) {
    REXLOG_WARN("Cannot load the original game font; using the built-in FPS font");
    config.SizePixels=28;
    return atlas->AddFontDefault(&config);
  }
  REXLOG_INFO("FPS overlay uses the original FOT-Rowdy outlines");
  return font;
}
std::unique_ptr<rex::ui::ImGuiDialog> CreateFpsOverlay(rex::ui::ImGuiDrawer* drawer,ImFont* font) {
  if(!font) return {};
  return std::make_unique<FpsOverlay>(drawer,font);
}
