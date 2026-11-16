#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico de offsets exactos para magia e items en tu version del juego."""
import os, sys, struct, ctypes, subprocess, time
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
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

def find_link_base(handle):
    """Encuentra la base de Link buscando max_health=80 (20 corazones)."""
    print("Buscando base de Link (salud=20 corazones)...")
    mbi = MEMORY_BASIC_INFORMATION64()
    curr = 0x10000
    max_addr = 0x7FFFFFFFFFFF
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100
    RW_MASK = 0x04 | 0x08 | 0x40 | 0x80
    chunk = 4 * 1024 * 1024

    while curr < max_addr:
        res = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(curr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not res or mbi.RegionSize == 0:
            break
        if (mbi.State == MEM_COMMIT and
                not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x1000):
            reg_base = mbi.BaseAddress
            reg_size = mbi.RegionSize
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
                                    base = addr + pos - 0x180
                                    print(f"  >>> BASE DE LINK: 0x{base:016X}")
                                    return base
                        pos += 4
                offset += read_len
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if next_addr <= curr:
            break
        curr = next_addr
    return None

def scan_fields(handle, base_link):
    """Busca offsets de magia e items en un rango desde la base de Link."""
    print("\nBuscando campos de magia e items desde la base de Link...")
    print("Rango: base + 0x000 hasta base + 0x5000")
    print()

    found = {}
    search_end = base_link + 0x5000
    chunk = 0x1000  # 4KB bloques

    addr = base_link
    while addr < search_end:
        read_len = min(chunk, search_end - addr)
        buf = ctypes.create_string_buffer(read_len)
        br = ctypes.c_size_t(0)
        res = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, ctypes.c_size_t(read_len), ctypes.byref(br))
        if not res or br.value == 0:
            addr += read_len
            continue
        data = buf.raw[:br.value]

        for i in range(0, len(data) - 4, 4):
            val = struct.unpack_from("<I", data, i)[0]
            abs_addr = addr + i
            rel_off = abs_addr - base_link
            if rel_off < 0 or rel_off > 0x5000:
                continue
            if rel_off in found.values():
                continue

            # Magia actual: 0-96 (barra doble = 96)
            if "cur_magic" not in found and 0 <= val <= 96:
                # Evitar falsos positivos con salud conocida
                if rel_off in (0x158, 0x180):
                    continue
                found["cur_magic"] = rel_off
                print(f"  [cur_magic={val}] Offset +0x{rel_off:04X}")

            # Magic flag: 1 o 2 (doble magia)
            if "magic_flag" not in found and val in (1, 2):
                if rel_off not in (0x158, 0x180):
                    found["magic_flag"] = rel_off
                    print(f"  [magic_flag={val}] Offset +0x{rel_off:04X}")

            # Max magic: 0x30 (48) o 0x60 (96)
            if "max_magic" not in found and val in (48, 96):
                if rel_off not in (0x158, 0x180):
                    found["max_magic"] = rel_off
                    print(f"  [max_magic={val}] Offset +0x{rel_off:04X}")

            # Items: valores entre 0 y 99 (excluyendo salud ya conocida)
            if "bombchus" not in found and 0 <= val <= 99:
                if rel_off not in (0x158, 0x180, found.get("cur_magic", -1), found.get("max_magic", -1), found.get("magic_flag", -1)):
                    found["bombchus"] = rel_off
                    print(f"  [bombchus={val}] Offset +0x{rel_off:04X}")

            if "deku_nuts" not in found and 0 <= val <= 99:
                if rel_off not in (0x158, 0x180, found.get("cur_magic", -1), found.get("max_magic", -1), found.get("magic_flag", -1), found.get("bombchus", -1)):
                    found["deku_nuts"] = rel_off
                    print(f"  [deku_nuts={val}] Offset +0x{rel_off:04X}")

            if "deku_seeds" not in found and 0 <= val <= 99:
                if rel_off not in (0x158, 0x180, found.get("cur_magic", -1), found.get("max_magic", -1), found.get("magic_flag", -1), found.get("bombchus", -1), found.get("deku_nuts", -1)):
                    found["deku_seeds"] = rel_off
                    print(f"  [deku_seeds={val}] Offset +0x{rel_off:04X}")

            if "deku_sticks" not in found and 0 <= val <= 99:
                if rel_off not in (0x158, 0x180, found.get("cur_magic", -1), found.get("max_magic", -1), found.get("magic_flag", -1), found.get("bombchus", -1), found.get("deku_nuts", -1), found.get("deku_seeds", -1)):
                    found["deku_sticks"] = rel_off
                    print(f"  [deku_sticks={val}] Offset +0x{rel_off:04X}")

            if "magic_beans" not in found and 0 <= val <= 99:
                if rel_off not in (0x158, 0x180, found.get("cur_magic", -1), found.get("max_magic", -1), found.get("magic_flag", -1), found.get("bombchus", -1), found.get("deku_nuts", -1), found.get("deku_seeds", -1), found.get("deku_sticks", -1)):
                    found["magic_beans"] = rel_off
                    print(f"  [magic_beans={val}] Offset +0x{rel_off:04X}")

        addr += read_len

    print()
    print("=" * 60)
    print("OFFSETS ENCONTRADOS PARA TU VERSION DEL JUEGO:")
    print("=" * 60)
    for field in ["cur_magic", "max_magic", "magic_flag", "bombchus", "deku_nuts", "deku_seeds", "deku_sticks", "magic_beans"]:
        if field in found:
            print(f'    "{field}": 0x{found[field]:04X},')
        else:
            print(f'    "{field}": None,  # No encontrado')
    print()
    print("Copia estos valores en STRUCT_OFFSETS de modmenu.py")

    kernel32.CloseHandle(handle)

def main():
    print("=" * 60)
    print("DIAGNOSTICO DE MAGIA E ITEMS")
    print("=" * 60)
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
        print("OpenProcess FALLO. Ejecuta como Administrador.")
        input("Presiona Enter...")
        return

    base_link = find_link_base(handle)
    if base_link:
        scan_fields(handle, base_link)

    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
