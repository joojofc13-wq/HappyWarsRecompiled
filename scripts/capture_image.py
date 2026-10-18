"""Read the guest image from a running ReXGlue codegen process for analysis.

Only reads memory, checks the target executable name and requires an MZ image.
No injection, no game execution and no dependency on an emulator.
"""
import argparse
import ctypes
import json
from pathlib import Path
from analyze import ROOT, xex_report


def capture(pid, xex):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    kernel.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)]
    kernel.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    process=kernel.OpenProcess(0x410,False,pid)
    if not process:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        name=ctypes.create_unicode_buffer(32768)
        length=ctypes.c_uint32(len(name))
        if not kernel.QueryFullProcessImageNameW(process,0,name,ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        if Path(name.value).name.lower()!='rexglue.exe':
            raise ValueError('Target is not rexglue.exe')
        report=xex_report(xex)
        guest_base=int(report['load_address'],16)
        # Virtual arena base observed in pinned SDK's codegen log.
        host_base=0x100000000+guest_base
        output=ctypes.create_string_buffer(report['image_size'])
        read=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(process,host_base,output,len(output),ctypes.byref(read)):
            raise ctypes.WinError(ctypes.get_last_error())
        if read.value!=len(output) or output.raw[:2]!=b'MZ':
            raise ValueError('Guest image not fully loaded at expected arena address')
        (ROOT/'private/loaded-image.bin').write_bytes(output.raw)
        (ROOT/'logs/image-capture.json').write_text(json.dumps(dict(pid=pid,tool=name.value,
            host_address=hex(host_base),guest_address=hex(guest_base),size=read.value,
            xex_sha256=report['sha256'],method='ReadProcessMemory; read-only snapshot after SDK load'),indent=2))
        print(f'Captured {read.value} bytes from SDK process {pid}')
    finally:
        kernel.CloseHandle(process)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pid',type=int)
    p.add_argument('--xex',type=Path,default=ROOT/'private/game/Default.xex')
    a=p.parse_args()
    capture(a.pid,a.xex)
