#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico integral: encuentra TODOS los offsets exactos de tu version."""
import os, sys, struct, ctypes, subprocess, time
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.ReadProcessMemory.restype = wintypes.BOOL

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
    except Exception:
        pass
    return None

def read_u32(handle, addr):
    buf = ctypes.create_string_buffer(4)
    br = ctypes.c_size_t(0)
    res = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, ctypes.c_size_t(4), ctypes.byref(br))
    if res and br.value == 4:
        return struct.unpack("<I", buf.raw)[0]
    return None

def main():
    print("=" * 60)
    print("DIAGNOSTICO INTEGRAL - Todos los offsets de Link")
    print("=" * 60)
    print()
    print("Valores que buscas: Rupias=200, Flechas=12, Bombas=3,")
    print("                    Corazones=20 (80 unidades), Magia=96")
    print()

    pid = find_pid()
    print(f"PID hookshot.exe: {pid if pid else 'NO ENCONTRADO'}")
    if not pid:
        print("El juego no esta ejecutandose. Carga tu partida primero.")
        input("Presiona Enter...")
        return

    handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
    if not handle:
        handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)
    if not handle:
        print("OpenProcess FALLO.")
        input("Presiona Enter...")
        return

    # Paso 1: Encontrar base de Link buscando max_health=80 y cur_health=80
    print("PASO 1: Buscando base de Link (salud=20 corazones)...")
    print()

    # Escanear todo el espacio RW
    class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_uint64), ("AllocationBase", ctypes.c_uint64),
            ("AllocationProtect", wintypes.DWORD), ("Alignment1", wintypes.DWORD),
            ("RegionSize", ctypes.c_uint64), ("State", wintypes.DWORD),
            ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
            ("Alignment2", wintypes.DWORD),
        ]

    mbi = MEMORY_BASIC_INFORMATION64()

    kernel32.VirtualQueryEx.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
    kernel32.VirtualQueryEx.restype = ctypes.c_size_t

    base_link = None
    curr = 0x10000
    max_addr = 0x7FFFFFFFFFFF
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100
    RW_MASK = 0x04 | 0x08 | 0x40 | 0x80

    scan_count = 0
    while curr < max_addr:
        res = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(curr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not res or mbi.RegionSize == 0:
            break
        if (mbi.State == MEM_COMMIT and
                not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x1000):
            reg_base = mbi.BaseAddress
            reg_size = mbi.RegionSize
            chunk = 4 * 1024 * 1024
            offset = 0
            while offset < reg_size:
                read_len = min(chunk, reg_size - offset)
                addr = reg_base + offset
                buf = ctypes.create_string_buffer(read_len)
                br = ctypes.c_size_t(0)
                res2 = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, ctypes.c_size_t(read_len), ctypes.byref(br))
                if res2 and br.value > 0:
                    data = buf.raw[:br.value]
                    max_off = len(data) - 8
                    pos = 0
                    while pos <= max_off:
                        if pos % 4 != 0:
                            pos += 4
                            continue
                        mh_val = struct.unpack_from("<I", data, pos)[0]
                        if mh_val == 80:  # 20 corazones * 4
                            if pos + 0x28 + 4 <= len(data):
                                ch_val = struct.unpack_from("<I", data, pos + 0x28)[0]
                                if ch_val == 80:  # 20 corazones actuales
                                    base_link = addr + pos - 0x180
                                    print(f"  >>> BASE DE LINK ENCONTRADA: 0x{base_link:016X}")
                                    print(f"     max_health en 0x{base_link + 0x180:016X} = {mh_val//4} corazones")
                                    print(f"     cur_health  en 0x{base_link + 0x158:016X} = {ch_val//4} corazones")
                                    break
                        pos += 4
                if base_link:
                    break
                offset += read_len
            if base_link:
                break
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if next_addr <= curr:
            break
        curr = next_addr
        scan_count += 1

    if not base_link:
        print("  No se encontro la base de Link. Asegurate de tener 20 corazones.")
        kernel32.CloseHandle(handle)
        input("Presiona Enter...")
        return

    print()
    print("PASO 2: Buscando offsets de todos los campos desde la base...")
    print()

    # Campos que buscamos con sus valores esperados
    targets = {
        "rupees": 200,
        "arrows": 12,
        "bombs": 3,
        "cur_magic": 96,
        "max_magic": 96,
        "magic_flag": 2,
        "cur_health": 80,
        "max_health": 80,
    }

    found_offsets = {}
    search_range = 0x5000  # Buscar hasta 20KB desde la base

    for off in range(0, search_range, 4):
        addr = base_link + off
        val = read_u32(handle, addr)
        if val is None:
            continue

        for field, expected in targets.items():
            if field not in found_offsets and val == expected:
                found_offsets[field] = off
                print(f"  [{field.upper()}={val}] Offset +0x{off:04X} (direccion 0x{addr:016X})")

    print()
    if found_offsets:
        print("=" * 60)
        print("TODOS LOS OFFSETS PARA TU VERSION DEL JUEGO:")
        print("=" * 60)
        for field in ["cur_health", "max_health", "rupees", "arrows", "bombs", "cur_magic", "max_magic", "magic_flag"]:
            if field in found_offsets:
                print(f'    "{field}": 0x{found_offsets[field]:04X},')
        print()
        print("Copia estos valores en STRUCT_OFFSETS de modmenu.py")
    else:
        print("No se encontraron coincidencias. Los valores pueden haber cambiado.")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
