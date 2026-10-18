#pragma once
#include <rex/ui/imgui_dialog.h>
#include <memory>
struct ImFont;
struct ImFontAtlas;
void InitializeFrameCounter();
ImFont* LoadGameFpsFont(ImFontAtlas* atlas);
std::unique_ptr<rex::ui::ImGuiDialog> CreateFpsOverlay(rex::ui::ImGuiDrawer* drawer,ImFont* font);
