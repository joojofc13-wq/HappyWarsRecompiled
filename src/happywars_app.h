// happywars - ReXGlue Recompiled Project
//
// Customize your app by overriding virtual hooks from rex::ReXApp.

#pragma once

#include <rex/rex_app.h>
#include <rex/runtime.h>
#include "verified_callbacks.h"
#include "local_http.h"
#include "crash_diagnostics.h"
#include "fps_overlay.h"
#include "performance.h"
#include <rex/ui/keybinds.h>
#include <rex/filesystem.h>
#include <rex/cvar.h>
#include <fstream>
#include <regex>
#include <chrono>
#include <random>

class HappyWarsApp : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(
      rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<HappyWarsApp>(new HappyWarsApp(ctx, "happywars",
        PPCImageConfig));
  }

  void OnPreSetup(rex::RuntimeConfig& config) override {
    ConfigureGamePerformance();
    if (config.gpu_plugin.empty()) config.gpu_plugin = "xenos";
  }
  void OnConfigurePaths(rex::PathConfig& paths) override {
    auto folder = rex::filesystem::GetExecutableFolder();
    if (std::filesystem::is_regular_file(folder / "game/Default.xex") &&
        std::filesystem::is_directory(folder / "game/media")) {
      if (paths.game_data_root.empty()) paths.game_data_root = folder / "game";
      if (rex::cvar::GetFlagByName("user_data_root").empty()) paths.user_data_root = folder / "saves";
      if (rex::cvar::GetFlagByName("cache_root").empty()) paths.cache_root = folder / "cache";
      rex::cvar::SetFlagByName("mnk_mode", "true");
      return;
    }

    for (unsigned depth = 0; depth < 4; ++depth, folder = folder.parent_path()) {
      if (!std::filesystem::is_regular_file(folder / "happywars_manifest.toml")) continue;
      if (paths.game_data_root.empty()) paths.game_data_root = folder / "private/game";
      auto read_text = [](const std::filesystem::path& file) {
        std::ifstream input(file);
        return std::string(std::istreambuf_iterator<char>(input), {});
      };
      if (rex::cvar::GetFlagByName("user_data_root").empty())
        paths.user_data_root = folder / "private/smoke-user";
      if (rex::cvar::GetFlagByName("cache_root").empty()) paths.cache_root = folder / "private/smoke-cache";
      const auto gpu = read_text(folder / "private/gpu-settings.json");
      for (const auto* key : {"d3d12_bindless", "d3d12_debug", "d3d12_tiled_shared_memory"}) {
        std::smatch match;
        if (std::regex_search(gpu, match, std::regex(std::string("\"") + key + "\"\\s*:\\s*(true|false)")))
          rex::cvar::SetFlagByName(key, match[1].str());
      }
      rex::cvar::SetFlagByName("mnk_mode", "true");
      break;
    }
  }
  void OnConfigureLogging(rex::LogConfig& config) override {
    // Explicit playtest-launcher paths take precedence; direct launches get a
    // new file instead of rotating over earlier crashes.
    if(rex::cvar::GetFlagSource("log_file")>=rex::cvar::Source::kEnvironment) return;
    const auto directory=rex::filesystem::GetExecutableFolder()/"logs/playtests";
    std::filesystem::create_directories(directory);
    const auto tick=std::chrono::system_clock::now().time_since_epoch().count();
    const auto name="run-"+std::to_string(tick)+"-"+std::to_string(std::random_device{}())+".log";
    config.log_file=directory/name;
    const auto path=config.log_file.u8string();
    rex::cvar::SetFlagByName("log_file",std::string(reinterpret_cast<const char*>(path.c_str()),path.size()));
  }
  void OnPostSetup() override {
    InitializeFrameCounter();
    RegisterVerifiedCallbacks(*runtime());
    InitializeLocalHttp(runtime()->user_data_root()/"title-storage.sqlite");
    auto fault=std::filesystem::u8path(rex::cvar::GetFlagByName("log_file"));
    if(fault.empty()) fault=runtime()->user_data_root()/"guest-fault.log";
    else fault.replace_extension(".guest-fault.log");
    InitializeCrashDiagnostics(fault);
    REXLOG_INFO("Happy Wars native build: local profile policy and title-check tracing enabled");
  }
  void OnConfigureFonts(ImFontAtlas* atlas) override {
    fps_font_=LoadGameFpsFont(atlas);
  }
  void OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) override {
    fps_overlay_=CreateFpsOverlay(drawer,fps_font_);
    rex::ui::RegisterBind("bind_fps_counter","F6","Toggle FPS counter",[this,drawer] {
      if(fps_overlay_) fps_overlay_.reset();
      else fps_overlay_=CreateFpsOverlay(drawer,fps_font_);
      REXLOG_INFO("FPS counter {}",fps_overlay_?"enabled":"disabled");
    });
  }
  void OnShutdown() override {
    rex::ui::UnregisterBind("bind_fps_counter");
    fps_overlay_.reset();
  }

 private:
  ImFont* fps_font_=nullptr;
  std::unique_ptr<rex::ui::ImGuiDialog> fps_overlay_;
  // Override virtual hooks for customization:
  // void OnPostInitLogging() override {}
  // void OnLoadXexImage(std::string& xex_image) override {}
  // void OnPostLoadXexImage() override {}
  // void OnPostSetup() override {}
  // void OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) override {}
  // std::unique_ptr<rex::ui::ImGuiDialog> CreateAchievementsOverlay() override;
  // std::unique_ptr<rex::ui::AchievementNotificationDialog>
  // CreateAchievementNotificationDialog() override;
  // void OnShutdown() override {}
  // void OnConfigurePaths(rex::PathConfig& paths) override {}
};
