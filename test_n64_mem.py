import ctypes
from ctypes import wintypes
import struct

kernel32 = ctypes.windll.kernel32
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.ReadProcessMemory.restype = wintypes.BOOL

# Find PID 7980
handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, 7980)
print("Handle:", hex(handle) if handle else "Failed")

def read_mem(addr, size):
    buf = ctypes.create_string_buffer(size)
    r = ctypes.c_size_t()
    if kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, ctypes.byref(r)):
        return buf.raw[:r.value]
    return None

if handle:
    # Test addresses:
    # 0x10008011A5D0 (N64 SaveContext)
    for a in [0x10008011A5D0, 0x10008015E660, 0x10008011B920]:
        data = read_mem(a, 64)
        print(f"Read at 0x{a:X}: {data.hex() if data else 'None'}")
    kernel32.CloseHandle(handle)
