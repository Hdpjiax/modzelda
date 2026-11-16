#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico rapido: verifica direcciones especificas de Link."""
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
    print("DIAGNOSTICO RAPIDO - Verificacion de direcciones")
    print("=" * 60)
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

    # Direcciones candidatas del DIAG_TODO previo
    # max_health estaba en 0x6EF91BD0, cur_health en 0x6EF91BF8, rupias en 0x6EF91BAC
    # Base = max_health - 0x180 = 0x6EF91A50
    candidate_base = 0x6EF91A50

    print(f"Verificando direccion base candidata: 0x{candidate_base:016X}")
    print()

    # Leer offsets desde la base
    offsets = {
        "max_health_1 (+0x180)": 0x180,
        "cur_health_1 (+0x158)": 0x158,
        "rupees (+0x134)": 0x134,
        "cur_magic (+0x190)": 0x190,
        "max_magic (+0x194)": 0x194,
        "arrows (+0x814)": 0x814,
        "bombs (+0x83C)": 0x83C,
    }

    for label, off in offsets.items():
        addr = candidate_base + off
        val = read_u32(handle, addr)
        if val is not None:
            if label.startswith("max_health") or label.startswith("cur_health"):
                print(f"  {label:30s} en 0x{addr:016X} = {val} unidades ({val//4} corazones)")
            else:
                print(f"  {label:30s} en 0x{addr:016X} = {val}")
        else:
            print(f"  {label:30s} en 0x{addr:016X} = NO LEGIBLE")

    # Verificar si max_health es valido
    mh = read_u32(handle, candidate_base + 0x180)
    ch = read_u32(handle, candidate_base + 0x158)
    rup = read_u32(handle, candidate_base + 0x134)

    print()
    if mh and 12 <= mh <= 80 and mh % 4 == 0 and ch and 0 < ch <= mh:
        print("=" * 60)
        print("ESTRUCTURA VALIDA ENCONTRADA")
        print(f"  Direccion BASE de Link: 0x{candidate_base:016X}")
        print(f"  max_health: {mh//4} corazones ({mh} unidades)")
        print(f"  cur_health: {ch//4} corazones ({ch} unidades)")
        print(f"  rupias: {rup}")
        print("=" * 60)
        print()
        print("Usa esta direccion en el Mod Menu:")
        print(f"  0x{candidate_base:X}")
    else:
        print()
        print("La direccion 0x6EF91A50 no tiene una estructura valida ahora.")
        print("Esto puede ser porque cambiaste de area o de edad en el juego.")
        print()
        print("Probando direcciones cercanas...")
        # Test a range around the candidate
        found = False
        for test_base in range(candidate_base - 0x1000, candidate_base + 0x1000, 0x1000):
            mh_t = read_u32(handle, test_base + 0x180)
            ch_t = read_u32(handle, test_base + 0x158)
            if mh_t and 12 <= mh_t <= 80 and mh_t % 4 == 0 and ch_t and 0 < ch_t <= mh_t:
                print(f"  ENCONTRADO en 0x{test_base:016X}! corazones={ch_t//4}/{mh_t//4}")
                found = True
                break
        if not found:
            print("  No se encontro en el rango cercano.")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
