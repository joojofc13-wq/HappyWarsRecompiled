#include "performance.h"
#include <rex/cvar.h>
#include <rex/filesystem.h>
#include <rex/logging.h>
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

void ConfigureGamePerformance() {
#if defined(HAPPYWARS_TU46)
  const auto file=rex::filesystem::GetExecutableFolder()/"HappyWars.ini";
  auto target=GetPrivateProfileIntW(L"Graphics",L"FrameRate",60,file.c_str());
  if(target!=30 && target!=60) {
    REXLOG_WARN("Unsupported FrameRate {}; using original 30 FPS pacing",target);
    target=30;
  }
  const auto source=rex::cvar::GetFlagSource("video_mode_refresh_rate");
  if(source<rex::cvar::Source::kEnvironment) {
    // TU46 presents every second guest vblank. Keep guest clocks unchanged;
    // only change the video refresh used by the original presentation waits.
    rex::cvar::SetFlagByName("video_mode_refresh_rate",target==60?"120":"60");
  }
  REXLOG_INFO("TU46 pacing: target {} FPS, guest video refresh {} Hz; 60 FPS timing remains experimental",
              target,rex::cvar::GetFlagByName("video_mode_refresh_rate"));
#endif
}
