#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico por VALOR: busca direcciones donde esten tus valores exactos."""
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
    print("DIAGNOSTICO POR VALOR - Buscar direcciones de tus valores")
    print("=" * 60)
    print()
    print("Buscando direcciones que contengan: Magia=96, MagicFlag=2")
    print("Tambien validaremos: Rupias=200, Flechas=12, Bombas=3")
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

    # Listar regiones RW y buscar valores específicos
    mbi = MEMORY_BASIC_INFORMATION64()
    curr = 0x10000
    max_addr = 0x7FFFFFFFFFFF
    MEM_COMMIT = 0x1000
    PAGE_NOACCESS = 0x01
    PAGE_GUARD = 0x100
    RW_MASK = 0x04 | 0x08 | 0x40 | 0x80

    # Valores a buscar (tu partida real)
    buscar = {
        200: "RUPIAS=200",
        12: "FLECHAS=12",
        3: "BOMBAS=3",
        96: "MAGIA=96 (barra doble)",
        2: "MAGIC_FLAG=2 (doble magia)",
        80: "SALUD=80 (20 corazones)",
    }

    encontrado = {v: [] for v in buscar.values()}

    print("Escaneando toda la memoria RW del proceso...")
    print("Esto puede tardar unos momentos...")
    print()

    chunk = 4 * 1024 * 1024
    regiones = 0

    while curr < max_addr:
        res = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(curr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not res or mbi.RegionSize == 0:
            break
        if (mbi.State == MEM_COMMIT and
                not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x1000):
            regiones += 1
            reg_base = mbi.BaseAddress
            reg_size = mbi.RegionSize
            offset = 0
            while offset < reg_size:
                read_len = min(chunk, reg_size - offset)
                addr = reg_base + offset
                data = read_mem(handle, addr, read_len)
                if data:
                    for valor, nombre in buscar.items():
                        pat = struct.pack("<I", valor)
                        pos = data.find(pat)
                        while pos != -1:
                            abs_addr = addr + pos
                            # Solo guardar direcciones que tengan sentido (no 0x00000000)
                            if abs_addr > 0x10000:
                                encontrado[nombre].append(abs_addr)
                                if len(encontrado[nombre]) <= 5:
                                    print(f"  [{nombre}] direccion 0x{abs_addr:016X}")
                            pos = data.find(pat, pos + 4)
                offset += read_len
        next_addr = mbi.BaseAddress + mbi.RegionSize
        if next_addr <= curr:
            break
        curr = next_addr

    print()
    print(f"Regiones RW escaneadas: {regiones}")
    print()

    print("=" * 60)
    print("RESULTADOS - Direcciones encontradas para cada valor:")
    print("=" * 60)
    for valor, nombre in buscar.items():
        dirs = encontrado[nombre]
        if dirs:
            # Mostrar la direccion mas frecuente o la primera
            print(f"  {nombre}:")
            for d in dirs[:10]:
                print(f"    0x{d:016X}")
            if len(dirs) > 10:
                print(f"    ... y {len(dirs) - 10} direcciones mas")
        else:
            print(f"  {nombre}: NO ENCONTRADO")

    print()
    print("NOTA: Si MAGIA=96 y MAGIC_FLAG=2 aparecen, esos son los offsets")
    print("que necesitas para STRUCT_OFFSETS en modmenu.py")

    kernel32.CloseHandle(handle)
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
