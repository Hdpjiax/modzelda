#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico de offsets exactos para tu version del juego.
Busca rupias=200, flechas=12, bombas=3 alrededor de la direccion base conocida."""
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
    print("DIAGNOSTICO DE OFFSETS - Buscando tus valores exactos")
    print("=" * 60)
    print()
    print("Buscando: Rupias=200, Flechas=12, Bombas=3")
    print()

    pid = find_pid()
    print(f"PID hookshot.exe: {pid if pid else 'NO ENCONTRADO'}")
    if not pid:
        print("El juego no esta ejecutandose.")
        input("Presiona Enter...")
        return

    handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
    if not handle:
        handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)
    if not handle:
        print("OpenProcess FALLO.")
        input("Presiona Enter...")
        return

    # Direccion base conocida del diagnostico previo
    base_link = 0x6EF91A50
    print(f"Base de Link conocida: 0x{base_link:016X}")
    print()

    # Escanear un rango amplio alrededor de la base (0x000 a 0x3000)
    print("Escaneando desde base + 0x000 hasta base + 0x3000...")
    print("Buscando campos que coincidan con tus valores reales")
    print()

    found_fields = {}
    search_range = 0x3000

    for off in range(0, search_range, 4):
        addr = base_link + off
        val = read_u32(handle, addr)
        if val is None:
            continue

        # Buscar rupias = 200
        if val == 200 and "rupees" not in found_fields:
            found_fields["rupees"] = off
            print(f"  [RUPIAS=200]  Offset +0x{off:04X}  (direccion 0x{addr:016X})")

        # Buscar flechas = 12
        if val == 12 and "arrows" not in found_fields:
            found_fields["arrows"] = off
            print(f"  [FLECHAS=12]  Offset +0x{off:04X}  (direccion 0x{addr:016X})")

        # Buscar bombas = 3
        if val == 3 and "bombs" not in found_fields:
            found_fields["bombs"] = off
            print(f"  [BOMBAS=3]    Offset +0x{off:04X}  (direccion 0x{addr:016X})")

        # Buscar salud maxima = 80 (20 corazones * 4)
        if val == 80 and "max_health" not in found_fields:
            found_fields["max_health"] = off
            print(f"  [MAX_HEALTH=80] Offset +0x{off:04X}  (direccion 0x{addr:016X})")

        # Buscar salud actual = 80 (20 corazones)
        if val == 80 and "cur_health" not in found_fields and off != found_fields.get("max_health", -1):
            found_fields["cur_health"] = off
            print(f"  [CUR_HEALTH=80] Offset +0x{off:04X}  (direccion 0x{addr:016X})")

    print()
    if found_fields:
        print("=" * 60)
        print("OFFSETS ENCONTRADOS PARA TU VERSION DEL JUEGO:")
        print("=" * 60)
        for field, off in found_fields.items():
            print(f"  {field}: +0x{off:04X}")
        print()
        print("Copia estos valores para actualizar STRUCT_OFFSETS en modmenu.py")
    else:
        print("No se encontraron coincidencias exactas en el rango buscado.")
        print("Esto puede ser porque:")
        print("  - Los valores en memoria cambian constantemente")
        print("  - La estructura esta en una direccion diferente ahora")
        print("  - Estabas en una pantalla diferente cuando tomaste la captura")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
