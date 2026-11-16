#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico FINAL: encuentra la estructura exacta de Link y sus offsets."""
import os, sys, struct, ctypes, subprocess, time
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
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
    except Exception:
        pass
    return None

def read_mem(handle, addr, size):
    buf = ctypes.create_string_buffer(size)
    br = ctypes.c_size_t(0)
    res = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, ctypes.c_size_t(size), ctypes.byref(br))
    if res and br.value == size:
        return buf.raw
    return None

def main():
    print("=" * 60)
    print("DIAGNOSTICO FINAL - Estructura de Link")
    print("=" * 60)
    print()

    pid = find_pid()
    print(f"PID hookshot.exe: {pid if pid else 'NO ENCONTRADO'}")
    if not pid:
        print("El juego no esta ejecutandose.")
        input("Presiona Enter...")
        return
    print()

    handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
    if not handle:
        handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)
    if not handle:
        print("OpenProcess FALLO. Ejecuta como Administrador.")
        input("Presiona Enter...")
        return
    print("Proceso abierto correctamente")
    print()

    # Listar todas las regiones RW
    mbi = MEMORY_BASIC_INFORMATION64()
    curr = 0x10000
    max_addr = 0x7FFFFFFFFFFF
    regions = []
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100
    RW_MASK = 0x04 | 0x08 | 0x40 | 0x80

    while curr < max_addr:
        res = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(curr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not res or mbi.RegionSize == 0:
            break
        if (mbi.State == MEM_COMMIT and
                not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x1000):
            regions.append((mbi.BaseAddress, mbi.RegionSize))
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if next_addr <= curr:
            break
        curr = next_addr

    print(f"Regiones RW: {len(regions)}")
    print()

    # Buscar pares de salud
    print("Buscando pares de salud (cur_health, max_health) separados por 0x28...")
    print("max_health debe ser 12-80, multiplo de 4, y cur_health <= max_health")
    print()

    chunk = 8 * 1024 * 1024
    best_match = None
    best_score = -1
    candidates = []

    for reg_base, reg_size in regions:
        offset = 0
        while offset < reg_size:
            read_len = min(chunk, reg_size - offset)
            addr = reg_base + offset
            data = read_mem(handle, addr, read_len)
            if not data or len(data) < 8:
                offset += read_len
                continue
            max_off = len(data) - 8
            pos = 0
            while pos <= max_off:
                if pos % 4 != 0:
                    pos += 4
                    continue
                mh_val = struct.unpack_from("<I", data, pos)[0]
                if 12 <= mh_val <= 80 and mh_val % 4 == 0:
                    if pos + 0x28 + 4 <= len(data):
                        ch_val = struct.unpack_from("<I", data, pos + 0x28)[0]
                        if 0 < ch_val <= mh_val:
                            abs_mh = addr + pos
                            abs_ch = addr + pos + 0x28
                            base = abs_mh - 0x180
                            # Ver rupias en base + 0x134
                            rup_off_from_base = 0x134
                            rup_abs = base + rup_off_from_base
                            rup_val = 0
                            rup_rel = rup_abs - addr
                            if 0 <= rup_rel and rup_rel + 4 <= len(data):
                                rup_val = struct.unpack_from("<I", data, rup_rel)[0]
                            score = 1000 + (rup_val if rup_val <= 9999 else 0)
                            candidates.append((base, abs_mh, abs_ch, ch_val, mh_val, rup_val, score))
                            if score > best_score:
                                best_score = score
                                best_match = (base, abs_mh, abs_ch, ch_val, mh_val, rup_val)
                pos += 4
            offset += read_len

    if best_match:
        base, abs_mh, abs_ch, ch, mh, rup = best_match
        print(f"=" * 60)
        print(f"MEJOR CANDIDATO (estructura de Link):")
        print(f"  Direccion BASE de Link: 0x{base:016X}")
        print(f"  max_health en:          0x{abs_mh:016X} = {mh//4} corazones ({mh} unidades)")
        print(f"  cur_health en:          0x{abs_ch:016X} = {ch//4} corazones ({ch} unidades)")
        print(f"  Rupias (base+0x134) en: 0x{base + 0x134:016X} = {rup}")
        print(f"=" * 60)
        print()
        print("COPIA ESTA DIRECCION Y PEGALA EN EL MOD MENU:")
        print(f"  Direccion manual: 0x{base:X}")
        print()
        print("Luego haz clic en 'Establecer' en el panel del escanear.")
        print()
        print("Otros candidatos encontrados:")
        for i, (b, amh, ach, chv, mhv, r, s) in enumerate(candidates[:10]):
            print(f"  #{i+1}: base=0x{b:016X} corazones={chv//4}/{mhv//4} rupias={r}")
    else:
        print("No se encontraron pares de salud validos.")
        print("Asegurate de estar en tu partida (no en pantalla de titulo).")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
