import ctypes
from ctypes import wintypes
import struct

kernel32 = ctypes.windll.kernel32

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.VirtualQueryEx.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
kernel32.VirtualQueryEx.restype = ctypes.c_size_t

kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.ReadProcessMemory.restype = wintypes.BOOL

class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_uint64),
        ("AllocationBase", ctypes.c_uint64),
        ("AllocationProtect", wintypes.DWORD),
        ("Alignment1", wintypes.DWORD),
        ("RegionSize", ctypes.c_uint64),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("Alignment2", wintypes.DWORD),
    ]

# Find PID 7980
h = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, 7980)
print("Handle:", hex(h) if h else f"Failed (err {kernel32.GetLastError()})")

sig = bytes.fromhex("04030201eb802d00d8750100")
matches = []

if h:
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION64()
    while kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        base = mbi.BaseAddress
        size = mbi.RegionSize
        state = mbi.State
        prot = mbi.Protect
        
        # Look in committed RW memory
        if state == 0x1000 and (prot & 0x04 or prot & 0x40) and size < 64 * 1024 * 1024:
            buf = ctypes.create_string_buffer(size)
            read = ctypes.c_size_t()
            if kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(read)):
                data = buf.raw[:read.value]
                pos = data.find(sig)
                while pos != -1:
                    matches.append(base + pos)
                    print(f"MATCH AT: 0x{base + pos:X}")
                    pos = data.find(sig, pos + len(sig))
                    
        addr = base + size
        if addr >= 0x7FFFFFFFFFFF:
            break
            
    print("Total matches:", len(matches))
    kernel32.CloseHandle(h)
