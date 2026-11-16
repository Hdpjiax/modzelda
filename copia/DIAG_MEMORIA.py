#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico detallado de lectura de memoria de Hookshot."""
import os, sys, struct, ctypes, subprocess, time
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetExitCodeProcess.restype = wintypes.BOOL
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

def find_pid():
    cmd = 'tasklist /FI "IMAGENAME eq hookshot.exe" /FO CSV /NH'
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        for line in out.strip().splitlines():
            parts = line.split('","')
            if len(parts) >= 2:
                pid_str = parts[1].replace('"', '').strip()
                if pid_str.isdigit():
                    return int(pid_str)
    except Exception as e:
        print(f"Error tasklist: {e}")
    return None

def main():
    print("=== DIAGNOSTICO DE MEMORIA HOOKSHOT ===")
    print()

    # 1. Verificar admin
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Ejecutando como Administrador: {'SI' if is_admin else 'NO'}")
        if not is_admin:
            print("AVISO: No eres administrador. Es posible que no puedas leer la memoria del juego.")
    except Exception as e:
        print(f"No se pudo verificar admin: {e}")
    print()

    # 2. Encontrar PID
    pid = find_pid()
    print(f"PID de hookshot.exe: {pid if pid else 'NO ENCONTRADO'}")
    if not pid:
        print("El juego no esta ejecutandose. Abre hookshot.exe primero.")
        input("Presiona Enter para salir...")
        return
    print()

    # 3. Abrir proceso
    handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
    if not handle:
        handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)
    if not handle:
        err = kernel32.GetLastError()
        print(f"OpenProcess FALLO (Error Win32 {err}). Ejecuta como Administrador.")
        input("Presiona Enter para salir...")
        return
    print(f"Proceso abierto correctamente. Handle: 0x{handle:X}")
    print()

    # 4. Escanear regiones RW del heap
    GUEST_HEAP_BASE = 0x1000000000
    max_heap = GUEST_HEAP_BASE + 0x1000000000

    mbi = MEMORY_BASIC_INFORMATION64()
    curr = GUEST_HEAP_BASE
    regions = []
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100
    RW_MASK = 0x04 | 0x08 | 0x40 | 0x80

    while curr < max_heap:
        res = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(curr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not res or mbi.RegionSize == 0:
            break
        if (mbi.State == MEM_COMMIT and
                not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x10000):
            regions.append((mbi.BaseAddress, mbi.RegionSize))
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if next_addr <= curr:
            break
        curr = next_addr

    print(f"Regiones RW comprometidas en el heap: {len(regions)}")
    total_mb = sum(s for _, s in regions) / (1024 * 1024)
    print(f"Memoria total escaneable: {total_mb:.1f} MB")
    print()

    # 5. Buscar firma de estructura de Link
    # Offset 0x134 = rupees, 0x814 = arrows, 0x158/0x180 = health pair
    STRUCT_OFFSETS = {
        "rupees": 0x134,
        "cur_health_1": 0x158,
        "max_health_1": 0x180,
        "arrows": 0x814,
        "bombs": 0x83C,
    }

    def check_struct(data, base_off):
        if base_off + 0xC28 > len(data):
            return False
        rup = struct.unpack_from("<I", data, base_off + 0x134)[0]
        if rup > 9999:
            return False
        arr = struct.unpack_from("<I", data, base_off + 0x814)[0]
        if arr > 9999:
            return False
        mh = struct.unpack_from("<I", data, base_off + 0x180)[0]
        ch = struct.unpack_from("<I", data, base_off + 0x158)[0]
        if not (12 <= mh <= 80 and mh % 4 == 0 and 0 < ch <= mh):
            return False
        return True

    print("Buscando estructura de Link en el heap...")
    found = False
    chunk = 4 * 1024 * 1024
    for reg_base, reg_size in regions:
        offset = 0
        while offset < reg_size:
            read_len = min(chunk, reg_size - offset)
            addr = reg_base + offset
            buf = ctypes.create_string_buffer(read_len)
            br = ctypes.c_size_t(0)
            res = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, ctypes.c_size_t(read_len), ctypes.byref(br))
            if res and br.value > 0:
                data = buf.raw[:br.value]
                max_off = len(data) - 0xC30
                for page_off in range(0, max_off + 1, 0x1000):
                    if check_struct(data, page_off):
                        abs_addr = addr + page_off
                        rup = struct.unpack_from("<I", data, page_off + 0x134)[0]
                        mh = struct.unpack_from("<I", data, page_off + 0x180)[0]
                        ch = struct.unpack_from("<I", data, page_off + 0x158)[0]
                        arr = struct.unpack_from("<I", data, page_off + 0x814)[0]
                        print(f"  >>> ESTRUCTURA ENCONTRADA en 0x{abs_addr:X}!")
                        print(f"      Corazones: {ch//4}/{mh//4}  Rupias: {rup}  Flechas: {arr}")
                        found = True
                        break
            if found:
                break
            offset += read_len
        if found:
            break

    if not found:
        print("  No se encontro la estructura de Link en ninguna region RW.")
        print("  Posibles causas:")
        print("   - Estoy en la pantalla de titulo (Continuar/Nueva partida)")
        print("   - Las direcciones de memoria han cambiado en esta version del juego")
        print("   - Falta permisos de administrador para leer memoria")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
