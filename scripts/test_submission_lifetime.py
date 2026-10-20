"""Compile fault-injection checks against the patched D3D12 fence code."""
import json
import pathlib
import subprocess

from build import ROOT, environment


def main():
    settings = json.loads((ROOT / "config/local-tools.json").read_text())
    source = (pathlib.Path(settings["rexglue_source"]) /
              "src/graphics/d3d12/command_processor.cpp").read_text()
    read_start = source.index("  auto read_completed = [this]()")
    read_end = source.index("  if (!read_completed()) return;", read_start)
    read_body = source[read_start:read_end] + "\nreturn read_completed();"
    gate_start = source.index("  const uint64_t queued_frames =")
    gate_end = source.index("  if (is_opening_frame) {", gate_start)
    gate_body = source[gate_start:gate_end] + "\nreturn true;"
    harness = r"""
#include <algorithm>
#define REXCVAR_GET(name) max_frames
int max_frames=3;
#define CHECK(value) do { if (!(value)) return __LINE__; } while (false)
#include <cstdint>
struct Device { int GetDeviceRemovedReason() { return -1; } };
struct Provider { Device device; Device* GetDevice() { return &device; } };
struct Fence { uint64_t value=0; uint64_t GetCompletedValue() { return value; } };
struct Graphics {
  bool notified=false;
  void OnHostGpuLossFromAnyThread(bool) { notified=true; }
};
struct Processor {
  Fence fence; Fence* submission_fence_=&fence;
  Graphics graphics; Graphics* graphics_system_=&graphics;
  Provider provider;
  bool device_removed_=false;
  uint64_t submission_completed_=7, frame_current_=3, waited=0;
  static constexpr unsigned kQueueFrames=3;
  uint64_t closed_frame_submissions_[3]={9,0,0};
  Provider& GetD3D12Provider() { return provider; }
  void LogDeviceRemovalDiagnostics(Device*,int) {}
  void CheckSubmissionFence(uint64_t value) { waited=value; }
  bool read() { READ_BODY }
  bool begin(bool is_opening_frame) { GATE_BODY }
};
int main() {
  Processor p;
  p.fence.value=UINT64_MAX;
  CHECK(!p.read());
  CHECK(p.submission_completed_==7);
  CHECK(p.device_removed_ && p.graphics.notified);
  CHECK(!p.begin(true) && !p.begin(false));
  Processor q;
  CHECK(!q.begin(true) && q.waited==9);
  CHECK(q.begin(false) && q.waited==0);
  q.fence.value=9;
  CHECK(q.read() && q.submission_completed_==9);
  CHECK(q.begin(true));
  q.fence.value=10;
  CHECK(q.read() && q.begin(true));
  q.closed_frame_submissions_[2]=11;
  max_frames=1;
  CHECK(!q.begin(true) && q.waited==11);
  q.fence.value=11;
  CHECK(q.read() && q.begin(true));
  q.frame_current_=1;
  q.closed_frame_submissions_[0]=0;
  CHECK(q.begin(true) && q.waited==0);
  max_frames=3;
  CHECK(q.begin(true) && q.waited==0);
}
"""
    harness = harness.replace("READ_BODY", read_body).replace("GATE_BODY", gate_body)
    output = ROOT / "build/submission-lifetime-test"
    output.mkdir(parents=True, exist_ok=True)
    cpp, exe = output / "test.cpp", output / "test.exe"
    cpp.write_text(harness)
    env = environment(settings)
    subprocess.run([settings["clang"], "--target=x86_64-pc-windows-msvc",
                    "-fms-runtime-lib=dll", "-std=c++20", str(cpp),
                    "-o", str(exe)], env=env, check=True)
    subprocess.run([str(exe)], env=env, check=True)
    print("Submission lifetime fault-injection checks passed.")


if __name__ == "__main__":
    main()
