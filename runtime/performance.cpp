#include "performance.h"
#include <rex/cvar.h>
#include <rex/logging.h>

void ConfigureGamePerformance() {
#if defined(HAPPYWARS_TU46)
  // Restore TU46's original video timing, including builds that saved the
  // experimental 120 Hz setting in their runtime configuration.
  rex::cvar::SetFlagByName("video_mode_refresh_rate","60");
  REXLOG_INFO("TU46 pacing: original 30 FPS target, 60 Hz guest video refresh");
#endif
}
