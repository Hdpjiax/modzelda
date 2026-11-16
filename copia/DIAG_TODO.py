#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico completo: escanea TODAS las regiones RW del proceso buscando estructura de Link."""
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
    print("DIAGNOSTICO COMPLETO - Escaneo de todo el espacio RW")
    print("=" * 60)
    print()

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Administrador: {'SI' if is_admin else 'NO'}")
    except:
        pass
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
        err = kernel32.GetLastError()
        print(f"OpenProcess FALLO (Error {err}).")
        input("Presiona Enter...")
        return
    print("Proceso abierto correctamente")
    print()

    # Escanear TODO el espacio de direcciones RW (desde 0x10000 hasta 0x7FFFFFFFFFFF)
    mbi = MEMORY_BASIC_INFORMATION64()
    curr = 0x10000
    max_addr = 0x7FFFFFFFFFFF
    regions = []
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100
    RW_MASK = 0x04 | 0x08 | 0x40 | 0x80

    print("Listando todas las regiones RW del proceso...")
    while curr < max_addr:
        res = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(curr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not res or mbi.RegionSize == 0:
            break
        if (mbi.State == MEM_COMMIT and
                not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x1000):
            regions.append((mbi.BaseAddress, mbi.RegionSize, mbi.Protect))
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if next_addr <= curr:
            break
        curr = next_addr

    print(f"Regiones RW encontradas: {len(regions)}")
    total_mb = sum(s for _, s, _ in regions) / (1024 * 1024)
    print(f"Memoria total RW: {total_mb:.1f} MB")
    print()

    # Mostrar las primeras 20 regiones para ver donde esta la memoria
    print("Primeras regiones (Base, Size, Protect):")
    for base, size, prot in regions[:20]:
        print(f"  0x{base:016X}  size=0x{size:X}  prot=0x{prot:04X}")
    if len(regions) > 20:
        print(f"  ... y {len(regions) - 20} regiones mas")
    print()

    # Buscar estructura de Link en todas las regiones
    print("Buscando pares de salud (cur_health, max_health) separados por 0x28...")
    print("Donde max_health es multiplo de 4 entre 12 y 80, y cur_health <= max_health")
    print()

    found_any = False
    candidates_found = 0
    chunk = 4 * 1024 * 1024

    for reg_base, reg_size, prot in regions:
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
                    pos += 1
                    continue
                mh_val = struct.unpack_from("<I", data, pos)[0]
                if 12 <= mh_val <= 80 and mh_val % 4 == 0:
                    if pos + 0x28 + 4 <= len(data):
                        ch_val = struct.unpack_from("<I", data, pos + 0x28)[0]
                        if 0 < ch_val <= mh_val:
                            abs_mh = addr + pos
                            abs_ch = addr + pos + 0x28
                            candidates_found += 1
                            if candidates_found <= 15:
                                print(f"  CANDIDATO #{candidates_found}:")
                                print(f"    max_health en 0x{abs_mh:016X} = {mh_val//4} corazones ({mh_val} unidades)")
                                print(f"    cur_health  en 0x{abs_ch:016X} = {ch_val//4} corazones ({ch_val} unidades)")
                                # Ver rupees en pos - 0x24
                                rup_off = pos - 0x24
                                if 0 <= rup_off and rup_off + 4 <= len(data):
                                    rup = struct.unpack_from("<I", data, rup_off)[0]
                                    if rup <= 9999:
                                        print(f"    Rupias en 0x{addr + rup_off:016X} = {rup}")
                                print()
                                found_any = True
                pos += 4
            offset += read_len

    if not found_any:
        print("  No se encontraron pares de salud en ninguna region RW.")
        print()
        print("POSIBLES CAUSAS:")
        print("  1. Estas en la pantalla de titulo (Continuar/Nueva partida)")
        print("     -> CARGA TU PARTIDA antes de escanear")
        print("  2. El juego puede estar en un estado donde Link no existe en memoria")
        print("  3. Los offsets de salud son diferentes en esta version")
    else:
        print(f"Total candidatos encontrados: {candidates_found}")
        print()
        print("La direccion base de Link = direccion de max_health menos 0x180")
        print("Ejemplo: si max_health esta en 0x1010XXXX, la base es 0x1010XXXX - 0x180")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
