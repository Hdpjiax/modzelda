#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico profundo: busca la estructura de Link probando offsets multiples."""
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
    print("DIAGNOSTICO PROFUNDO - Estructura de Link en memoria")
    print("=" * 60)
    print()

    # Admin check
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Administrador: {'SI' if is_admin else 'NO'}")
        if not is_admin:
            print("  -> EJECUTA COMO ADMINISTRADOR para leer memoria del juego")
    except:
        pass
    print()

    # PID
    pid = find_pid()
    print(f"PID hookshot.exe: {pid if pid else 'NO ENCONTRADO'}")
    if not pid:
        print("El juego no esta ejecutandose.")
        input("Presiona Enter...")
        return
    print()

    # Abrir proceso
    handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
    if not handle:
        handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)
    if not handle:
        err = kernel32.GetLastError()
        print(f"OpenProcess FALLO (Error {err}). Ejecuta como Administrador.")
        input("Presiona Enter...")
        return
    print("Proceso abierto correctamente")
    print()

    # Listar regiones RW del heap
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

    print(f"Regiones RW en heap: {len(regions)}")
    total_mb = sum(s for _, s in regions) / (1024 * 1024)
    print(f"Memoria total: {total_mb:.1f} MB")
    print()

    # Buscar patrones de salud: un par (cur_health, max_health) separados por 0x28
    # donde max_health sea multiplo de 4 entre 12 y 80, y cur_health <= max_health
    print("Buscando pares de salud (cur, max) separados por 0x28 bytes...")
    print()

    found_any = False
    chunk = 4 * 1024 * 1024
    candidates_found = 0

    for reg_base, reg_size in regions:
        offset = 0
        while offset < reg_size:
            read_len = min(chunk, reg_size - offset)
            addr = reg_base + offset
            data = read_mem(handle, addr, read_len)
            if not data or len(data) < 0x100:
                offset += read_len
                continue

            # Buscar en cada alineacion de 4 bytes
            max_off = len(data) - 8
            pos = 0
            while pos <= max_off:
                if pos % 4 != 0:
                    pos += 1
                    continue
                # Leer posible max_health en pos
                mh_val = struct.unpack_from("<I", data, pos)[0]
                # max_health debe ser 12-80, multiplo de 4
                if 12 <= mh_val <= 80 and mh_val % 4 == 0:
                    # Leer cur_health en pos + 0x28
                    if pos + 0x28 + 4 <= len(data):
                        ch_val = struct.unpack_from("<I", data, pos + 0x28)[0]
                        if 0 < ch_val <= mh_val:
                            # Candidato encontrado
                            abs_mh = addr + pos
                            abs_ch = addr + pos + 0x28
                            candidates_found += 1
                            if candidates_found <= 10:
                                print(f"  CANDIDATO #{candidates_found}:")
                                print(f"    max_health (0x180) en 0x{abs_mh:X} = {mh_val//4} corazones ({mh_val} unidades)")
                                print(f"    cur_health  (0x158) en 0x{abs_ch:X} = {ch_val//4} corazones ({ch_val} unidades)")
                                # Verificar si hay rupees en pos - 0x28 (0x158 - 0x24 = 0x134)
                                rup_off = pos - 0x24
                                if 0 <= rup_off and rup_off + 4 <= len(data):
                                    rup = struct.unpack_from("<I", data, rup_off)[0]
                                    if rup <= 9999:
                                        print(f"    Rupias (0x134) en 0x{addr + rup_off:X} = {rup}")
                                print()
                                found_any = True
                pos += 4
            offset += read_len

    if not found_any:
        print("  No se encontraron pares de salud en el heap.")
        print()
        print("POSIBLES CAUSAS:")
        print("  1. Estas en la pantalla de titulo (Continuar/Nueva partida) - carga tu partida")
        print("  2. Los offsets de memoria cambiaron en esta version del juego")
        print("  3. El juego usa ASLR y las direcciones son diferentes cada sesion")
        print("  4. Falta permisos de administrador")
    else:
        print(f"Total candidatos encontrados: {candidates_found}")
        print()
        print("Si ves candidatos arriba, la direccion de max_health es la base de la estructura.")
        print("Usa esa direccion menos 0x180 como direccion base de Link en el escaneo manual.")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
