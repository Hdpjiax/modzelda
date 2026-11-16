#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  THE LEGEND OF ZELDA: OCARINA OF TIME — TRIFORCE MOD MENU (v4.8)
  Interfaz rediseñada tipo menú de Switch 2 + escáner dinámico de la
  estructura de Link en memoria (base 0x1000000000 del guest).
===============================================================================
"""

import os
import sys
import json
import time
import struct
import ctypes
from ctypes import wintypes
import threading
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from ztk import *

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

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
kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.WriteProcessMemory.restype = wintypes.BOOL
kernel32.VirtualProtectEx.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_size_t, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
kernel32.VirtualProtectEx.restype = wintypes.BOOL

psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
psapi.EnumProcessModules.restype = wintypes.BOOL
psapi.GetModuleBaseNameA.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_char_p, wintypes.DWORD]
psapi.GetModuleBaseNameA.restype = wintypes.DWORD

# Constantes y RVAs del motor nativo (hookshot.exe / hookshot_vk.dll)
RVA_PROTECT_HEARTS = 0x9B5830    # uint32: 1 = Modo Dios / Protección de corazones en hookshot_vk.dll
RVA_PLAYER_FLIGHT  = 0xFFDA64    # uint8:  1 = Vuelo libre / No-clip con doble salto
RVA_LINK_SPEED     = 0x9B5758    # uint32: Índice de velocidad de Link (0=1.0x, 1=1.25x, 2=1.5x, 3=2.0x)
RVA_CHEAT_ACTION   = 0x100250C   # uint32: Disparador de acciones del motor
RVA_ITEMS_TABLE    = 0xF24F50    # Tabla de 90 ítems del juego
RVA_ITEM_COUNTS    = 0xFFD910    # Cantidades y munición por ítem
RVA_EXE_PROTECT    = 0x232C30D0  # hos_oot_protect_hearts en hookshot.exe (Modo Dios)
RVA_EXE_ACTION     = 0x232C35C8  # hos_oot_live_action en hookshot.exe (Trigger de cheats)
GUEST_SAVECONTEXT  = 0x100080CD0EA0
GUEST_N64_CTX      = 0x10008011A5D0

# RVAs exactos del estado de Link en hookshot_vk.dll
RVA_VK_RUPEES      = 0x9B5614    # uint32: Rupias vivas (0..9999)
RVA_VK_HEARTS      = 0x9B562C    # uint32: Corazones actuales (20)
RVA_VK_MAX_HEARTS  = 0x9B58C0    # uint32: Corazones máximos (20)
RVA_VK_MAGIC       = 0x9B5644    # uint32: Magia actual (0..96)
RVA_VK_BOMBS       = 0x9B568C    # uint32: Bombas vivas (3)
RVA_VK_BEANS       = 0x9B56C8    # uint32: Judías mágicas (2)
RVA_VK_ARROWS      = 0x9B57C8    # uint32: Flechas vivas (12)
RVA_VK_STICKS      = 0x9B57D0    # uint32: Palos Deku (4)

# RVAs del inventario de munición / cantidades en hookshot_vk.dll
RVA_ITEM_STICKS    = 0xFFD93C    # uint32: Palos Deku
RVA_ITEM_NUTS      = 0xFFD940    # uint32: Nueces Deku
RVA_ITEM_BOMBS     = 0xFFD944    # uint32: Bombas
RVA_ITEM_BOMBCHUS  = 0xFFD948    # uint32: Bombchus
RVA_ITEM_SEEDS     = 0xFFD950    # uint32: Semillas tirachinas
RVA_ITEM_ARROWS    = 0xFFD958    # uint32: Flechas
RVA_ITEM_BEANS     = 0xFFDA90    # uint32: Semillas / Judías Mágicas

# Direcciones directas en el Guest Heap de Link (100% funcionales para HUD y Magia viva)
GUEST_HEAP_HOST_BASE = 0x101000000000
ADDR_MAGIC_ACTOR_1   = GUEST_HEAP_HOST_BASE + 0x4E040F08  # uint32: Magia viva del Actor Link
ADDR_HEARTS_ACTOR_1  = GUEST_HEAP_HOST_BASE + 0x4E040EF8  # uint32: Salud viva (20 corazones)
ADDR_MAGIC_ACTOR_2   = GUEST_HEAP_HOST_BASE + 0x4E1A0F08  # uint32: Magia viva del Actor Link (secundaria)
ADDR_HEARTS_ACTOR_2  = GUEST_HEAP_HOST_BASE + 0x4E1A0EF8  # uint32: Salud viva (20 corazones)
ADDR_MAGIC_HUD       = GUEST_HEAP_HOST_BASE + 0x6851F67C  # uint32: Medidor de magia visual en HUD
ADDR_HEARTS_HUD      = GUEST_HEAP_HOST_BASE + 0x6851F668  # uint32: Corazones visuales en HUD
ADDR_MAGIC_ACTOR_3   = GUEST_HEAP_HOST_BASE + 0x09B1D1A8  # uint32: Magia activa (clúster 3)
ADDR_HEARTS_ACTOR_3  = GUEST_HEAP_HOST_BASE + 0x09B1D1B8  # uint32: Salud activa (80 unidades = 20 corazones)


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


class LiveLogger:
    def __init__(self, log_file_path="triforce_modmenu_debug.log"):
        self.log_file_path = os.path.abspath(log_file_path)
        self.entries = []
        self.listeners = []
        self._lock = threading.Lock()
        try:
            with open(self.log_file_path, "w", encoding="utf-8") as f:
                f.write(f"=== Zelda OoT Triforce Mod Menu Log ({datetime.now().isoformat()}) ===\n")
        except Exception:
            pass

    def add_listener(self, callback):
        self.listeners.append(callback)

    def log(self, level, msg):
        now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{now_str}] [{level}] {msg}"
        with self._lock:
            self.entries.append((level, line))
            if len(self.entries) > 600:
                self.entries.pop(0)
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass
        for listener in list(self.listeners):
            try:
                listener(level, line)
            except Exception:
                pass

    def info(self, msg): self.log("INFO", msg)
    def ok(self, msg):   self.log("OK", msg)
    def warn(self, msg): self.log("WARN", msg)
    def err(self, msg):  self.log("ERR", msg)


# =============================================================================
# COMUNICACIÓN IPC CON EL MOTOR (PIPE NATIVO) — puente original de v4.7
# =============================================================================
class HookshotNativeBridge:
    def __init__(self, logger: LiveLogger):
        self.log = logger
        self.socket_path = r"\\.\pipe\hookshot_control"
        self._pipe_lock = threading.Lock()

    def send_cmd(self, payload):
        msg_str = json.dumps(payload) + "\n"
        with self._pipe_lock:
            try:
                with open(self.socket_path, "r+b", buffering=0) as pipe:
                    pipe.write(msg_str.encode("utf-8"))
                    pipe.flush()
                    reply = pipe.readline().decode("utf-8", errors="ignore").strip()
                    if reply:
                        return True, json.loads(reply)
            except Exception:
                pass
        return False, {}

    def get_status(self):
        ok, res = self.send_cmd({"cmd": "status"})
        return res if ok else None

    def teleport(self, dest_idx, target_age=None):
        if target_age in ("child", "adult"):
            self.send_cmd({"cmd": "age", "to": target_age})
            time.sleep(0.04)
        ok, reply = self.send_cmd({"cmd": "teleport", "to": int(dest_idx)})
        if ok and reply.get("ok"):
            dest_name = reply.get("child") or reply.get("adult") or f"Destino #{dest_idx}"
            return True, f"¡Teletransportado a {dest_name} con éxito!"
        msg = reply.get("message", "Teletransporte rechazado por el juego.")
        return False, msg

    def set_age(self, age_str):
        ok, reply = self.send_cmd({"cmd": "age", "to": age_str})
        if ok and reply.get("ok"):
            return True, f"¡Transformado en Link {age_str.upper()}!"
        return False, reply.get("message", "No se pudo cambiar la edad.")

    def set_option(self, key, value):
        ok, reply = self.send_cmd({"cmd": "option_set", "name": key, "value": value})
        return ok and reply.get("ok", False)


# =============================================================================
# MAPA DE MEMORIA DEL GUEST (estándar Hookshot / OoT Switch 2)
# =============================================================================
GUEST_HEAP_BASE  = 0x1000000000
STRUCT_OFFSETS = {
    "rupees":       0x134,   # uint32 (0..9999) - pendiente de confirmar en tu version
    "cur_health_1": 0x158,   # uint32 (4 unidades = 1 corazón) - CONFIRMADO
    "cur_health_2": 0x15C,
    "cur_health_3": 0x160,
    "max_health_1": 0x180,   # uint32 - CONFIRMADO
    "max_health_2": 0x184,
    "max_health_3": 0x188,
    "cur_magic":    None,    # pendiente de detección dinámica
    "max_magic":    None,
    "magic_flag":   None,
    "arrows":       0x110,   # uint32 - CONFIRMADO en tu version
    "bombs":        0xEC,    # uint32 - CONFIRMADO en tu version
    "bombchus":     None,
    "deku_nuts":    None,
    "deku_seeds":   None,
    "deku_sticks":  None,
    "magic_beans":  None,
}
OFFSET_CHEAT_FLAGS = 0x04E9FF80

TELEPORT_LOCATIONS = [
    {"idx": 0, "cat": "Ciudades y Aldeas",   "name": "Bosque Kokiri",                   "map": "KokiriForest"},
    {"idx": 1, "cat": "Ciudades y Aldeas",   "name": "Pradera de Hyrule",               "map": "HyruleField"},
    {"idx": 2, "cat": "Ciudades y Aldeas",   "name": "Aldea Kakariko",                  "map": "KakarikoVillage"},
    {"idx": 3, "cat": "Ciudades y Aldeas",   "name": "Mercado de la Ciudadela",         "map": "Market"},
    {"idx": 4, "cat": "Afueras de Templos",  "name": "Afueras del Gran Árbol Deku",     "map": "SacredForestMeadow"},
    {"idx": 5, "cat": "Afueras de Templos",  "name": "Afueras de la Cueva Dodongo",     "map": "DeathMountainTrail"},
    {"idx": 6, "cat": "Afueras de Templos",  "name": "Afueras del Templo del Bosque",   "map": "SacredForestMeadow"},
    {"idx": 7, "cat": "Afueras de Templos",  "name": "Afueras del Templo del Fuego",    "map": "DeathMountainCrater"},
    {"idx": 8, "cat": "Afueras de Templos",  "name": "Afueras del Templo del Agua",     "map": "HyruleField"},
    {"idx": 9,  "cat": "Afueras de Templos", "name": "Afueras del Templo de la Sombra", "map": "Graveyard"},
    {"idx": 10,"cat": "Afueras de Templos",  "name": "Afueras del Templo del Espíritu", "map": "DesertColossus"},
    {"idx": 11,"cat": "Regiones y Ciudades", "name": "Bosque Perdido",                  "map": "LostWood"},
    {"idx": 12,"cat": "Regiones y Ciudades", "name": "Pradera Sagrada del Bosque",      "map": "SacredForestMeadow"},
    {"idx": 13,"cat": "Regiones y Ciudades", "name": "Rancho Lon Lon",                  "map": "HyruleField"},
    {"idx": 14,"cat": "Regiones y Ciudades", "name": "Cementerio de Kakariko",          "map": "Graveyard"},
    {"idx": 15,"cat": "Regiones y Ciudades", "name": "Sendero de la Montaña de la Muerte","map":"DeathMountainTrail"},
    {"idx": 16,"cat": "Regiones y Ciudades", "name": "Cráter de la Montaña de la Muerte","map":"DeathMountainCrater"},
    {"idx": 17,"cat": "Regiones y Ciudades", "name": "Ciudad Goron",                   "map": "GoronCity"},
    {"idx": 18,"cat": "Regiones y Ciudades", "name": "Río de los Zora",                "map": "ZoraRiver"},
    {"idx": 19,"cat": "Regiones y Ciudades", "name": "Región de los Zora",              "map": "ZoraDomain"},
    {"idx": 20,"cat": "Regiones y Ciudades", "name": "Fuente de los Zora",              "map": "ZoraFountain"},
    {"idx": 21,"cat": "Regiones y Ciudades", "name": "Valle Gerudo",                   "map": "GerudoValley"},
    {"idx": 22,"cat": "Regiones y Ciudades", "name": "Fortaleza Gerudo",               "map": "GerudoFortress"},
    {"idx": 23,"cat": "Regiones y Ciudades", "name": "Desierto Encantado",             "map": "HountedWasteland"},
    {"idx": 24,"cat": "Regiones y Ciudades", "name": "Coloso del Desierto",            "map": "DesertColossus"},
    {"idx": 25,"cat": "Interiores",          "name": "Interior del Gran Árbol Deku",    "map": "InsideTheDekuTree"},
    {"idx": 26,"cat": "Interiores",          "name": "Interior de la Cueva Dodongo",    "map": "DodongoCavern"},
    {"idx": 27,"cat": "Interiores",          "name": "Interior de la Barriga de Jabu","map":"InsideJabuJabuBelly"},
    {"idx": 28,"cat": "Interiores",          "name": "Interior del Templo del Bosque",   "map":"ForestTemple"},
    {"idx": 29,"cat": "Interiores",          "name": "Interior del Templo del Fuego",    "map":"FireTemple"},
    {"idx": 30,"cat": "Interiores",          "name": "Interior del Templo del Agua",     "map":"WaterTemple"},
    {"idx": 31,"cat": "Interiores",          "name": "Interior del Templo de la Sombra", "map":"ShadowTemple"},
    {"idx": 32,"cat": "Interiores",          "name": "Interior del Templo del Espíritu", "map":"SpiritTemple"},
    {"idx": 33,"cat": "Interiores",          "name": "Interior del Fondo del Pozo",      "map":"BottomOfTheWell"},
    {"idx": 34,"cat": "Interiores",          "name": "Interior de la Caverna de Hielo",  "map":"IceCavern"},
    {"idx": 35,"cat": "Interiores",          "name": "Interior del Centro Gerudo",       "map":"GerudoTrainingGround"},
    {"idx": 36,"cat": "Interiores",          "name": "Interior del Castillo de Ganon",   "map":"InsideGanonCastle"},
]

# =============================================================================
# MOTOR DE MEMORIA DINÁMICO (portado del v3.0 que SÍ funcionaba)
# Localiza la estructura de Link escaneando el heap del guest en tiempo real.
# =============================================================================
class ProcessMemoryEngine:
    def __init__(self, logger: LiveLogger):
        self.log = logger
        self.pid = None
        self.process_handle = None
        self.player_struct_addr = None
        self.health_max_addr = None   # direccion dinamica de max_health
        self.health_cur_addr = None   # direccion dinamica de cur_health
        self.active_health_slot = 1
        self.struct_verified = False
        self._warned_title_screen = False
        self._last_pid_poll = 0.0
        self._last_auto_probe = 0.0
        self.is_windows = sys.platform.startswith("win")
        self._known_max_health_addrs = []
        self.exe_base = None
        self.vk_dll_base = None
        # Direcciones dinamicas para otros campos (buscadas por bloque coordinado)
        self.rupees_addr = None
        self.arrows_addr = None
        self.bombs_addr = None
        self.cur_magic_addr = None
        self.magic_flag_addr = None
        self.max_magic_addr = None
        self.bombchus_addr = None
        self.deku_nuts_addr = None
        self.deku_seeds_addr = None
        self.deku_sticks_addr = None
        self.magic_beans_addr = None

    def _bind_vk_pointers(self):
        """Asigna todas las direcciones de salud, magia, rupias y 9 ítems directamente desde hookshot_vk.dll."""
        if not self.vk_dll_base:
            return
        self.rupees_addr = self.vk_dll_base + RVA_VK_RUPEES
        self.health_cur_addr = self.vk_dll_base + RVA_VK_HEARTS
        self.health_max_addr = self.vk_dll_base + RVA_VK_MAX_HEARTS
        self.cur_magic_addr = self.vk_dll_base + RVA_VK_MAGIC
        self.max_magic_addr = self.vk_dll_base + RVA_VK_MAGIC
        self.deku_sticks_addr = self.vk_dll_base + RVA_ITEM_STICKS
        self.deku_nuts_addr = self.vk_dll_base + RVA_ITEM_NUTS
        self.bombs_addr = self.vk_dll_base + RVA_ITEM_BOMBS
        self.bombchus_addr = self.vk_dll_base + RVA_ITEM_BOMBCHUS
        self.deku_seeds_addr = self.vk_dll_base + RVA_ITEM_SEEDS
        self.arrows_addr = self.vk_dll_base + RVA_ITEM_ARROWS
        self.magic_beans_addr = self.vk_dll_base + RVA_ITEM_BEANS
        self.player_struct_addr = self.rupees_addr
        self.struct_verified = True

    def locate_modules(self):
        """Localiza de forma ultrarrápida hookshot.exe y hookshot_vk.dll."""
        if not self.is_attached():
            return None
        if self.exe_base and self.vk_dll_base:
            return self.vk_dll_base
        hMods = (ctypes.c_void_p * 1024)()
        cbNeeded = wintypes.DWORD()
        if psapi.EnumProcessModules(ctypes.c_void_p(self.process_handle), hMods, ctypes.sizeof(hMods), ctypes.byref(cbNeeded)):
            nMods = cbNeeded.value // ctypes.sizeof(ctypes.c_void_p)
            modname = ctypes.create_string_buffer(260)
            for i in range(nMods):
                mod = hMods[i]
                if mod:
                    psapi.GetModuleBaseNameA(ctypes.c_void_p(self.process_handle), ctypes.c_void_p(mod), modname, 260)
                    name = modname.value.decode("ascii", errors="ignore").lower()
                    if name == "hookshot.exe":
                        self.exe_base = mod
                    elif "hookshot_vk" in name:
                        self.vk_dll_base = mod
                        self._bind_vk_pointers()
        if self.vk_dll_base and not self.struct_verified:
            self._bind_vk_pointers()
        return self.vk_dll_base

    def is_attached(self):
        if not self.process_handle or not self.is_windows:
            return False
        exit_code = wintypes.DWORD()
        res = kernel32.GetExitCodeProcess(ctypes.c_void_p(self.process_handle), ctypes.byref(exit_code))
        return bool(res and exit_code.value == 259)

    def find_hookshot_pid(self):
        if not self.is_windows:
            return None
        try:
            cmd = 'tasklist /FI "IMAGENAME eq hookshot.exe" /FO CSV /NH'
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

    def attach(self, force_rescan=False):
        if self.is_attached():
            # Si ya estamos conectados pero no hay estructura verificada, reintentar localizarla
            if force_rescan or (not self.struct_verified and self.player_struct_addr is None):
                self.verify_and_locate_player_struct(silent_if_menu=False)
            return self.is_attached()
        # Si ya sabemos el PID, reusarlo sin llamar a tasklist otra vez
        if self.pid:
            handle = kernel32.OpenProcess(0x1F0FFF, False, self.pid)
            if not handle:
                handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, self.pid)
            if handle:
                self.process_handle = handle
                self.log.ok(f"Re-conectado a Hookshot [PID: {self.pid}]")
                self.verify_and_locate_player_struct(silent_if_menu=False)
                return True
            self.pid = None
        pid = self.find_hookshot_pid()
        if not pid:
            self.detach()
            return False
        handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
        if not handle:
            handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)
        if not handle:
            return False
        self.pid = pid
        self.process_handle = handle
        self.log.ok(f"Conectado al proceso de Hookshot [PID: {pid}]")
        self.verify_and_locate_player_struct(silent_if_menu=False)
        return True

    def detach(self):
        if self.process_handle and self.is_windows:
            try:
                kernel32.CloseHandle(ctypes.c_void_p(self.process_handle))
            except Exception:
                pass
        self.process_handle = None
        self.pid = None
        self.struct_verified = False

    def read_bytes(self, address, size):
        if not self.is_attached() or not address or size <= 0:
            return None
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        res = kernel32.ReadProcessMemory(
            ctypes.c_void_p(self.process_handle), ctypes.c_void_p(address),
            buf, ctypes.c_size_t(size), ctypes.byref(bytes_read))
        if res and bytes_read.value > 0:
            return buf.raw[:bytes_read.value]
        return None

    def write_bytes(self, address, data):
        if not self.is_attached() or not address or not data:
            return False
        buf = ctypes.create_string_buffer(data, len(data))
        bytes_written = ctypes.c_size_t(0)
        PAGE_EXECUTE_READWRITE = 0x40
        old_protect = wintypes.DWORD(0)
        res = kernel32.WriteProcessMemory(
            ctypes.c_void_p(self.process_handle), ctypes.c_void_p(address),
            buf, ctypes.c_size_t(len(data)), ctypes.byref(bytes_written))
        if not res or bytes_written.value != len(data):
            try:
                kernel32.VirtualProtectEx.argtypes = [
                    wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
                ]
                kernel32.VirtualProtectEx.restype = wintypes.BOOL
                kernel32.VirtualProtectEx(
                    ctypes.c_void_p(self.process_handle), ctypes.c_void_p(address),
                    ctypes.c_size_t(len(data)), PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                res = kernel32.WriteProcessMemory(
                    ctypes.c_void_p(self.process_handle), ctypes.c_void_p(address),
                    buf, ctypes.c_size_t(len(data)), ctypes.byref(bytes_written))
            except Exception:
                pass
        return bool(res and bytes_written.value == len(data))

    def write_u32(self, address, val):
        return self.write_bytes(address, struct.pack("<I", int(val) & 0xFFFFFFFF))

    def write_u16(self, address, val):
        return self.write_bytes(address, struct.pack("<H", int(val) & 0xFFFF))

    def write_u8(self, address, val):
        return self.write_bytes(address, struct.pack("B", int(val) & 0xFF))

    def read_u32(self, address):
        raw = self.read_bytes(address, 4)
        if raw and len(raw) == 4:
            return struct.unpack("<I", raw)[0]
        return None

    def read_u16(self, address):
        raw = self.read_bytes(address, 2)
        if raw and len(raw) >= 2:
            return struct.unpack("<H", raw[:2])[0]
        return None

    def read_u8(self, address):
        raw = self.read_bytes(address, 1)
        if raw and len(raw) >= 1:
            return raw[0]
        return None

    # ---- escáner de la estructura de Link (heurística del v3.0) ----
    def _check_struct_buffer(self, data, base_offset, known_rupees=None, known_hearts=None, known_arrows=None):
        if base_offset < 0 or (base_offset + 0xC28) > len(data):
            return False, 0, 1, 0, 0, 0, 0
        rup_val = struct.unpack_from("<I", data, base_offset + 0x134)[0]
        if rup_val > 9999:
            return False, 0, 1, 0, 0, 0, 0
        if known_rupees is not None and rup_val != known_rupees:
            return False, 0, 1, 0, 0, 0, 0
        arr_val  = struct.unpack_from("<I", data, base_offset + 0x814)[0]
        bmb_val  = struct.unpack_from("<I", data, base_offset + 0x83C)[0]
        chu_val  = struct.unpack_from("<I", data, base_offset + 0x8DC)[0]
        nut_val  = struct.unpack_from("<I", data, base_offset + 0xA1C)[0]
        seed_val = struct.unpack_from("<I", data, base_offset + 0xA44)[0]
        stk_val  = struct.unpack_from("<I", data, base_offset + 0xA6C)[0]
        bean_val = struct.unpack_from("<I", data, base_offset + 0xC24)[0]
        if any(v > 9999 for v in (arr_val, bmb_val, chu_val, nut_val, seed_val, stk_val, bean_val)):
            return False, 0, 1, 0, 0, 0, 0
        if known_arrows is not None and arr_val != known_arrows:
            return False, 0, 1, 0, 0, 0, 0
        target_mh = int(known_hearts * 4) if known_hearts else None
        best_slot = 0
        best_ch = 0
        best_mh = 0
        matched_pairs = 0
        for idx, (c_off, m_off) in enumerate([(0x158, 0x180), (0x15C, 0x184), (0x160, 0x188)], start=1):
            ch = struct.unpack_from("<I", data, base_offset + c_off)[0]
            mh = struct.unpack_from("<I", data, base_offset + m_off)[0]
            if 12 <= mh <= 80 and (mh % 4 == 0) and (0 < ch <= mh):
                if target_mh is None or mh == target_mh:
                    matched_pairs += 1
                    if best_slot == 0:
                        best_slot, best_ch, best_mh = idx, ch, mh
        if best_slot == 0:
            return False, 0, 1, 0, 0, 0, 0
        non_zero_items = sum(1 for v in (rup_val, arr_val, bmb_val, chu_val, nut_val, seed_val, stk_val) if 0 < v <= 999)
        if non_zero_items == 0 and matched_pairs < 2 and known_hearts is None and known_rupees is None and known_arrows is None:
            return False, 0, 1, 0, 0, 0, 0
        score = (matched_pairs * 100 + non_zero_items * 25 +
                 (500 if known_hearts is not None and best_mh == target_mh else 0) +
                 (500 if known_arrows is not None and arr_val == known_arrows else 0) +
                 (500 if known_rupees is not None and rup_val == known_rupees else 0))
        return True, score, best_slot, best_ch, best_mh, rup_val, arr_val

    def _is_valid_player_struct(self, base_addr):
        raw = self.read_bytes(base_addr, 0xC30)
        if not raw or len(raw) < 0xC28:
            return False
        ok, _score, slot, _ch, _mh, _rup, _arr = self._check_struct_buffer(raw, 0)
        if ok:
            self.active_health_slot = slot
        return ok

    def verify_and_locate_player_struct(self, silent_if_menu=False):
        if not self.is_attached():
            return False
        if self.struct_verified and self.player_struct_addr:
            val = self.read_u32(self.player_struct_addr)
            if val is not None:
                return True
        return self.scan_coordinated_block()

    def scan_coordinated_block(self, known_rupees=None, known_hearts=None, known_arrows=None, known_bombs=None):
        """Escáner coordinado ultrarrápido y robusto.
        Verifica primero la estructura de Link en hookshot_vk.dll y escanea el heap si es requerido."""
        if not self.is_attached():
            self.attach()
        if not self.is_attached():
            self.log.err("No hay proceso de Hookshot conectado para escanear.")
            return False

        t0 = time.time()
        self.locate_modules()

        # 1. Si hookshot_vk.dll está cargado, verificar inmediatamente los datos del jugador
        if self.vk_dll_base:
            self._bind_vk_pointers()
            live_rup = self.read_u32(self.rupees_addr)
            live_hp = self.read_u32(self.health_cur_addr)
            live_mag = self.read_u32(self.cur_magic_addr)
            live_arr = self.read_u32(self.arrows_addr)
            live_bmb = self.read_u32(self.bombs_addr)

            # Si no hay filtros específicos o si coinciden con los datos en vivo del motor:
            matches_filter = True
            if known_rupees is not None and live_rup != known_rupees: matches_filter = False
            if known_hearts is not None and live_hp != known_hearts: matches_filter = False
            if known_arrows is not None and live_arr != known_arrows: matches_filter = False
            if known_bombs is not None and live_bmb != known_bombs: matches_filter = False

            if matches_filter or (known_rupees is None and known_hearts is None and known_arrows is None and known_bombs is None):
                dt = time.time() - t0
                self.log.ok(f"Estructura de Link verificada en hookshot_vk.dll (0x{self.rupees_addr:012X}) en {dt:.3f}s")
                self.log.ok(f"  Rupias={live_rup}, Salud={live_hp} corazones, Magia={live_mag}/96, Flechas={live_arr}, Bombas={live_bmb}")
                self.struct_verified = True
                self._warned_title_screen = False
                return True

        filters_desc = []
        if known_rupees is not None: filters_desc.append(f"Rupias={known_rupees}")
        if known_hearts is not None: filters_desc.append(f"Corazones={known_hearts}")
        if known_arrows is not None: filters_desc.append(f"Flechas={known_arrows}")
        if known_bombs is not None: filters_desc.append(f"Bombas={known_bombs}")
        self.log.info(f"Buscando bloque en memoria del juego | Filtros: {', '.join(filters_desc) if filters_desc else 'Detección automática'}...")

        addr = 0x10000
        mbi = MEMORY_BASIC_INFORMATION64()
        regions = []
        priority_prefixes = (0x0062, 0x0063, 0x01B1, 0x01F1, 0x01F2, 0x01F3, 0x1000, 0x107F)

        while kernel32.VirtualQueryEx(ctypes.c_void_p(self.process_handle), ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            base = mbi.BaseAddress
            size = mbi.RegionSize
            state = mbi.State
            prot = mbi.Protect

            if state == 0x1000 and (prot & 0x04 or prot & 0x40) and not (prot & 0x100):
                if 0x1000 <= size <= 64 * 1024 * 1024:
                    if (base >> 32) != 0x6E: # Excluir decodificador AMD Radeon
                        pref = base >> 32
                        prio = 0 if pref in priority_prefixes else 1
                        regions.append((prio, base, size))
            addr = base + size
            if addr >= 0x7FFFFFFFFFFF:
                break

        regions.sort(key=lambda r: (r[0], r[2]))

        p_rup32 = struct.pack('<I', known_rupees) if known_rupees is not None else None
        p_rup16 = struct.pack('<H', known_rupees) if known_rupees is not None else None
        p_arr32 = struct.pack('<I', known_arrows) if known_arrows is not None else None
        p_arr16 = struct.pack('<H', known_arrows) if known_arrows is not None else None
        p_arr8  = bytes([known_arrows]) if known_arrows is not None else None
        p_bmb32 = struct.pack('<I', known_bombs) if known_bombs is not None else None
        p_bmb8  = bytes([known_bombs]) if known_bombs is not None else None

        target_hp_vals = []
        if known_hearts is not None:
            target_hp_vals = [known_hearts, known_hearts * 4, known_hearts * 16]

        chunk_sz = 8 * 1024 * 1024
        buf = ctypes.create_string_buffer(chunk_sz)
        read = ctypes.c_size_t(0)

        best_candidate = None
        best_score = 0

        anchor_pat = p_rup32 or p_rup16 or p_arr32 or p_arr16

        if anchor_pat:
            for prio, base, size in regions:
                for off in range(0, size, chunk_sz):
                    rlen = min(chunk_sz, size - off)
                    if not kernel32.ReadProcessMemory(ctypes.c_void_p(self.process_handle), ctypes.c_void_p(base + off), buf, rlen, ctypes.byref(read)):
                        continue
                    nread = read.value
                    if nread < 0x200:
                        continue
                    data = buf.raw[:nread]

                    idx = 0
                    while True:
                        pos = data.find(anchor_pat, idx)
                        if pos == -1:
                            break
                        idx = pos + len(anchor_pat)

                        w_start = max(0, pos - 0x400)
                        w_end = min(nread, pos + 0x400)
                        win = data[w_start:w_end]

                        score = 200
                        found_fields = {"anchor": base + off + pos}

                        if known_arrows is not None:
                            if p_arr32 and p_arr32 in win:
                                score += 300
                                found_fields["arrows"] = base + off + w_start + win.find(p_arr32)
                            elif p_arr16 and p_arr16 in win:
                                score += 200
                                found_fields["arrows"] = base + off + w_start + win.find(p_arr16)
                            elif p_arr8 and p_arr8 in win:
                                score += 100
                                found_fields["arrows"] = base + off + w_start + win.find(p_arr8)

                        if known_bombs is not None:
                            if p_bmb32 and p_bmb32 in win:
                                score += 300
                                found_fields["bombs"] = base + off + w_start + win.find(p_bmb32)
                            elif p_bmb8 and p_bmb8 in win:
                                score += 150
                                found_fields["bombs"] = base + off + w_start + win.find(p_bmb8)

                        for hp_val in target_hp_vals:
                            p_hp32 = struct.pack('<I', hp_val)
                            p_hp16 = struct.pack('<H', hp_val)
                            if p_hp32 in win:
                                score += 300
                                found_fields["health"] = base + off + w_start + win.find(p_hp32)
                                break
                            elif p_hp16 in win:
                                score += 200
                                found_fields["health"] = base + off + w_start + win.find(p_hp16)
                                break

                        if score > best_score:
                            best_score = score
                            best_candidate = (base + off + pos, score, found_fields)
                            if score >= 800:
                                break
                    if best_candidate and best_score >= 800:
                        break
                if best_candidate and best_score >= 800:
                    break

        dt = time.time() - t0
        if best_candidate and best_score >= 400:
            c_addr, c_score, c_fields = best_candidate
            self.player_struct_addr = c_addr
            self.rupees_addr = c_addr
            if "arrows" in c_fields: self.arrows_addr = c_fields["arrows"]
            if "bombs" in c_fields: self.bombs_addr = c_fields["bombs"]
            if "health" in c_fields:
                self.health_cur_addr = c_fields["health"]
                self.health_max_addr = c_fields["health"]
            self.struct_verified = True
            self._warned_title_screen = False
            self.log.ok(f"Estructura localizada en 0x{c_addr:012X} en {dt:.2f}s (Puntaje: {c_score})")
            return True
        elif self.vk_dll_base:
            self._bind_vk_pointers()
            self.log.ok(f"Sincronizado directamente con hookshot_vk.dll (Rupias={self.read_u32(self.rupees_addr)})")
            return True
        else:
            self.log.warn(f"Escaneo ({dt:.2f}s) no encontró bloque con los valores dados.")
            return False

    def scan_player_struct(self, known_rupees=None, known_hearts=None, known_arrows=None, known_bombs=None):
        return self.scan_coordinated_block(known_rupees, known_hearts, known_arrows, known_bombs)

    def scan_player_struct_dynamic(self, known_rupees=None, known_hearts=None, known_arrows=None, known_bombs=None):
        return self.scan_coordinated_block(known_rupees, known_hearts, known_arrows, known_bombs)

    def read_active_health(self):
        if self.health_cur_addr:
            val = self.read_u32(self.health_cur_addr)
            if val is not None:
                if 1 <= val <= 20:
                    return val * 4, 80
                elif 21 <= val <= 80:
                    return val, 80
                elif 81 <= val <= 320:
                    return val // 4, 80
        if self.player_struct_addr:
            ch = self.read_u32(self.player_struct_addr + 0x264)
            if ch is not None and 1 <= ch <= 20:
                return ch * 4, 80
        return 80, 80

        slot_map = {1: (0x158, 0x180), 2: (0x15C, 0x184), 3: (0x160, 0x188)}
        order = [self.active_health_slot] + [s for s in (1, 2, 3) if s != self.active_health_slot]
        for s in order:
            c_off, m_off = slot_map[s]
            ch = self.read_u32(base + c_off)
            mh = self.read_u32(base + m_off)
            if ch is not None and mh is not None and (12 <= mh <= 80) and (mh % 4 == 0):
                self.active_health_slot = s
                return ch, mh
        return 0, 0

    def get_field_addr(self, field_name):
        if field_name in ("cur_health_1", "cur_health_2", "cur_health_3"):
            if self.health_cur_addr: return self.health_cur_addr
            if self.player_struct_addr: return self.player_struct_addr + 0x264
        if field_name in ("max_health_1", "max_health_2", "max_health_3"):
            if self.health_max_addr: return self.health_max_addr
            if self.player_struct_addr: return self.player_struct_addr + 0x3B0
        if field_name == "rupees":
            if self.rupees_addr: return self.rupees_addr
            if self.player_struct_addr: return self.player_struct_addr
        if field_name == "arrows":
            if self.arrows_addr: return self.arrows_addr
            if self.player_struct_addr: return self.player_struct_addr - 0x148
        if field_name == "bombs":
            if self.bombs_addr: return self.bombs_addr
            if self.player_struct_addr: return self.player_struct_addr - 0x1AC
        if field_name in ("cur_magic", "max_magic", "magic_flag"):
            if self.cur_magic_addr: return self.cur_magic_addr
            if self.player_struct_addr: return self.player_struct_addr + 0x270
        offset = STRUCT_OFFSETS.get(field_name)
        if offset is None or self.player_struct_addr is None:
            return 0
        return self.player_struct_addr + offset

    def _enumerate_committed_rw_regions(self, include_all_address_space=False):
        heap_regions = []
        other_regions = []
        min_heap = GUEST_HEAP_BASE
        max_heap = GUEST_HEAP_BASE + 0x1000000000
        if self.is_windows:
            kernel32.VirtualQueryEx.argtypes = [
                ctypes.c_void_p, ctypes.c_void_p,
                ctypes.POINTER(MEMORY_BASIC_INFORMATION64), ctypes.c_size_t]
            kernel32.VirtualQueryEx.restype = ctypes.c_size_t
            mbi = MEMORY_BASIC_INFORMATION64()
            curr = 0x10000 if include_all_address_space else min_heap
            max_addr = 0x7FFFFFFFFFFF if include_all_address_space else max_heap
            MEM_COMMIT = 0x1000
            PAGE_NOACCESS = 0x01
            PAGE_GUARD = 0x100
            RW_MASK = 0x04 | 0x08 | 0x40 | 0x80
            while curr < max_addr:
                res = kernel32.VirtualQueryEx(
                    ctypes.c_void_p(self.process_handle), ctypes.c_void_p(curr),
                    ctypes.byref(mbi), ctypes.sizeof(mbi))
                if not res or mbi.RegionSize == 0:
                    break
                if (mbi.State == MEM_COMMIT and
                        not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and
                        (mbi.Protect & RW_MASK) and mbi.RegionSize >= 0x10000):
                    if min_heap <= mbi.BaseAddress < max_heap:
                        heap_regions.append((mbi.BaseAddress, mbi.RegionSize))
                    elif include_all_address_space:
                        other_regions.append((mbi.BaseAddress, mbi.RegionSize))
                next_addr = mbi.BaseAddress + mbi.RegionSize
                if next_addr <= curr:
                    break
                curr = next_addr
        return heap_regions + other_regions


# =============================================================================
# CONTROLADOR PRINCIPAL DE CHEATS EN TIEMPO REAL
# =============================================================================
class TriforceModController:
    def __init__(self, logger: LiveLogger):
        self.log = logger
        self.mem = ProcessMemoryEngine(logger)
        self.bridge = HookshotNativeBridge(logger)

        self.god_mode = False
        self.inf_health = False
        self.inf_magic = False
        self.no_clip_flight = False
        self.inf_rupees_ammo = False
        self.damage_mult = 1.0
        self.link_speed_idx = 0
        self.game_speed_idx = 1

        self.live_fps = 0.0
        self.live_map = "Conectando..."
        self.live_age = "ADULTO"

        self.live_cur_hp = 80
        self.live_max_hp = 80
        self.live_magic = 0
        self.live_rupees = 0
        self.live_arrows = 0
        self.live_bombs = 0
        self.live_nuts = 0
        self.live_sticks = 0
        self.live_seeds = 0
        self.live_bombchus = 0
        self.live_beans = 0

        self.is_running = True
        self._thread = threading.Thread(target=self._realtime_loop, daemon=True)
        self._thread.start()

    def _realtime_loop(self):
        status_timer = 0.0
        attach_timer = 0.0
        while self.is_running:
            now = time.time()
            if now - status_timer >= 0.5:
                status_timer = now
                st = self.bridge.get_status()
                if st and st.get("ok"):
                    self.live_fps = float(st.get("fps", 0.0))
                    self.live_map = str(st.get("map", "HyruleField"))
                    self.live_age = str((st.get("game") or {}).get("age", "adult")).upper()

            # Intentar conectar al juego si no estamos conectados
            if not self.mem.is_attached() and now - attach_timer >= 2.0:
                attach_timer = now
                self.mem.attach()

            if self.mem.is_attached():
                self.mem.locate_modules()
                # Gestión continua de Modo Dios: si está apagado, forzar explícitamente 0
                if self.god_mode:
                    if self.mem.exe_base:
                        self.mem.write_u32(self.mem.exe_base + RVA_EXE_PROTECT, 1)
                    if self.mem.vk_dll_base:
                        self.mem.write_u32(self.mem.vk_dll_base + RVA_PROTECT_HEARTS, 1)
                    self.mem.write_u16(GUEST_N64_CTX + 0, 320)
                    self.mem.write_u16(GUEST_N64_CTX + 2, 320)
                    self.mem.write_u32(ADDR_HEARTS_HUD, 20)
                    self.mem.write_u32(ADDR_HEARTS_ACTOR_1, 20)
                    self.mem.write_u32(ADDR_HEARTS_ACTOR_2, 20)
                else:
                    if self.mem.exe_base:
                        self.mem.write_u32(self.mem.exe_base + RVA_EXE_PROTECT, 0)
                    if self.mem.vk_dll_base:
                        self.mem.write_u32(self.mem.vk_dll_base + RVA_PROTECT_HEARTS, 0)

                # Gestión continua de Magia Infinita (Barra Doble Verde al 100%)
                if self.inf_magic:
                    self.mem.write_u8(GUEST_N64_CTX + 4, 2)
                    self.mem.write_u8(GUEST_N64_CTX + 5, 96)
                    self.mem.write_u8(GUEST_N64_CTX + 6, 96)
                    self.mem.write_u8(GUEST_N64_CTX + 7, 1)
                    self.mem.write_u8(GUEST_N64_CTX + 8, 1)
                    self.mem.write_u8(GUEST_N64_CTX + 9, 0)
                    self.mem.write_u8(GUEST_N64_CTX + 0x14 + 4, 2)
                    self.mem.write_u8(GUEST_N64_CTX + 0x14 + 5, 96)
                    self.mem.write_u8(GUEST_N64_CTX + 0x14 + 6, 96)
                    self.mem.write_u8(GUEST_N64_CTX + 0x14 + 7, 1)
                    self.mem.write_u8(GUEST_N64_CTX + 0x14 + 8, 1)
                    for a in (ADDR_MAGIC_ACTOR_1, ADDR_MAGIC_ACTOR_2, ADDR_MAGIC_HUD):
                        self.mem.write_u32(a, 96)
                    if self.mem.cur_magic_addr:
                        self.mem.write_u32(self.mem.cur_magic_addr, 96)

                # Telemetría en vivo de salud y magia directa de SaveContext y HUD
                live_mag = self.mem.read_u8(GUEST_N64_CTX + 5)
                if live_mag is None or live_mag == 0:
                    live_mag = self.mem.read_u32(ADDR_MAGIC_HUD)
                self.live_magic = live_mag if (live_mag is not None and live_mag > 0) else 96

                live_hp_raw = self.mem.read_u16(GUEST_N64_CTX + 2)
                if live_hp_raw is not None and live_hp_raw > 0:
                    self.live_cur_hp = live_hp_raw // 4
                else:
                    live_hp = self.mem.read_u32(ADDR_HEARTS_HUD)
                    if live_hp is not None and live_hp > 0:
                        self.live_cur_hp = (live_hp * 4) if live_hp <= 20 else live_hp

                max_hp = self.mem.read_u32(self.mem.health_max_addr) if self.mem.health_max_addr else None
                if max_hp is not None:
                    self.live_max_hp = (max_hp * 4) if max_hp <= 20 else max_hp

            if self.mem.is_attached() and self.mem.struct_verified:
                if self.mem.rupees_addr:
                    self.live_rupees = self.mem.read_u32(self.mem.rupees_addr) or 0
                if self.mem.arrows_addr:
                    self.live_arrows = self.mem.read_u32(self.mem.arrows_addr) or 0
                if self.mem.bombs_addr:
                    self.live_bombs = self.mem.read_u32(self.mem.bombs_addr) or 0
                if self.mem.deku_nuts_addr:
                    self.live_nuts = self.mem.read_u32(self.mem.deku_nuts_addr) or 0
                if self.mem.deku_sticks_addr:
                    self.live_sticks = self.mem.read_u32(self.mem.deku_sticks_addr) or 0
                if self.mem.deku_seeds_addr:
                    self.live_seeds = self.mem.read_u32(self.mem.deku_seeds_addr) or 0
                if self.mem.bombchus_addr:
                    self.live_bombchus = self.mem.read_u32(self.mem.bombchus_addr) or 0
                if self.mem.magic_beans_addr:
                    self.live_beans = self.mem.read_u32(self.mem.magic_beans_addr) or 0

                if self.inf_health:
                    self.mem.write_u16(GUEST_N64_CTX + 0, 320)
                    self.mem.write_u16(GUEST_N64_CTX + 2, 320)
                    for a in (ADDR_HEARTS_ACTOR_1, ADDR_HEARTS_ACTOR_2, ADDR_HEARTS_HUD):
                        self.mem.write_u32(a, 20)
                    if self.mem.health_cur_addr:
                        self.mem.write_u32(self.mem.health_cur_addr, 20)

                if self.inf_rupees_ammo:
                    if self.mem.rupees_addr:
                        self.mem.write_u32(self.mem.rupees_addr, 9999)
                    if self.mem.arrows_addr:
                        self.mem.write_u32(self.mem.arrows_addr, 99)
                    if self.mem.bombs_addr:
                        self.mem.write_u32(self.mem.bombs_addr, 99)
                    if self.mem.deku_nuts_addr:
                        self.mem.write_u32(self.mem.deku_nuts_addr, 99)
                    if self.mem.deku_sticks_addr:
                        self.mem.write_u32(self.mem.deku_sticks_addr, 99)
                    if self.mem.deku_seeds_addr:
                        self.mem.write_u32(self.mem.deku_seeds_addr, 99)
                    if self.mem.bombchus_addr:
                        self.mem.write_u32(self.mem.bombchus_addr, 99)
                    if self.mem.magic_beans_addr:
                        self.mem.write_u32(self.mem.magic_beans_addr, 99)

            time.sleep(0.04)

    def _refill_heap_clusters(self):
        """Escanea rápidamente los clústeres activos del Guest Heap y rellena cualquier medidor o actor de magia/salud."""
        if not self.mem.is_attached():
            return
        search_ranges = [
            (0x10104E000000, 2 * 1024 * 1024),   # Clúster de Actores Link
            (0x101068500000, 1 * 1024 * 1024),   # Clúster de HUD y medidores
            (0x101009B00000, 1 * 1024 * 1024),   # Clúster de Estado del Jugador
        ]
        for base_addr, sz in search_ranges:
            raw = self.mem.read_bytes(base_addr, sz)
            if not raw:
                continue
            p = 0
            while True:
                p = raw.find(b"\x60\x00\x00\x00", p)
                if p == -1:
                    break
                if p % 4 == 0:
                    surr = raw[max(0, p - 32):min(len(raw), p + 48)]
                    if (b"\x14\x00\x00\x00" in surr) or (b"\x50\x00\x00\x00" in surr):
                        for rel in (-32, -28, -24, -20, -16, -12, -8, -4, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40):
                            cur_p = p + rel
                            if 0 <= cur_p < len(raw) - 3:
                                val = struct.unpack("<I", raw[cur_p:cur_p + 4])[0]
                                if 1 <= val < 96:
                                    self.mem.write_u32(base_addr + cur_p, 96 if val <= 95 else 20)
                p += 4

    def apply_instant_magic_refill(self):
        """Aplica relleno instantáneo de magia doble al 100% en SaveContext, HUD y actores vivos."""
        if not self.mem.is_attached():
            self.mem.attach()
        if not self.mem.is_attached():
            return False
        # 1) Escribir en SaveContext en memoria N64 / Host
        self.mem.write_u8(GUEST_N64_CTX + 4, 2)   # Magic level 2 (Barra Doble)
        self.mem.write_u8(GUEST_N64_CTX + 5, 96)  # Magia actual (96/96)
        self.mem.write_u8(GUEST_N64_CTX + 6, 96)  # Capacidad máxima (96)
        self.mem.write_u8(GUEST_N64_CTX + 7, 1)   # isMagicAcquired
        self.mem.write_u8(GUEST_N64_CTX + 8, 1)   # isDoubleMagicAcquired
        self.mem.write_u8(GUEST_N64_CTX + 9, 0)   # magicState
        # Slot 2 espejo
        self.mem.write_u8(GUEST_N64_CTX + 0x14 + 4, 2)
        self.mem.write_u8(GUEST_N64_CTX + 0x14 + 5, 96)
        self.mem.write_u8(GUEST_N64_CTX + 0x14 + 6, 96)
        self.mem.write_u8(GUEST_N64_CTX + 0x14 + 7, 1)
        self.mem.write_u8(GUEST_N64_CTX + 0x14 + 8, 1)
        # 2) Escribir en actores y HUD del Guest Heap
        for a in (ADDR_MAGIC_ACTOR_1, ADDR_MAGIC_ACTOR_2, ADDR_MAGIC_HUD):
            self.mem.write_u32(a, 96)
        if self.mem.cur_magic_addr:
            self.mem.write_u32(self.mem.cur_magic_addr, 96)
        # 3) Enviar también vía pipe por seguridad
        try:
            self.bridge.send_cmd({"cmd": "mem_write", "addr": 0x8011A5D4, "hex": "026060010100"})
        except Exception:
            pass
        self.live_magic = 96
        return True

    def apply_instant_god_mode(self, enable: bool):
        """Activa o desactiva la protección nativa del motor de Hookshot (Modo Dios)."""
        if not self.mem.is_attached():
            self.mem.attach()
        if not self.mem.is_attached():
            return False
        val = 1 if enable else 0
        if self.mem.exe_base:
            self.mem.write_u32(self.mem.exe_base + RVA_EXE_PROTECT, val)
        if self.mem.vk_dll_base:
            self.mem.write_u32(self.mem.vk_dll_base + RVA_PROTECT_HEARTS, val)
        if enable:
            self.mem.write_u16(GUEST_N64_CTX + 0, 320)  # Max HP = 20 corazones
            self.mem.write_u16(GUEST_N64_CTX + 2, 320)  # Cur HP = 20 corazones
            self.mem.write_u32(ADDR_HEARTS_HUD, 20)
            self.mem.write_u32(ADDR_HEARTS_ACTOR_1, 20)
            self.mem.write_u32(ADDR_HEARTS_ACTOR_2, 20)
            self.live_cur_hp = 80
            self.live_max_hp = 80
        return True
        if self.mem.cur_magic_addr:
            self.mem.write_u32(self.mem.cur_magic_addr, 96)

        self.live_cur_hp = 80
        self.live_max_hp = 80
        self.live_magic = 96

        self.log.ok("💖 ¡Salud (20 corazones) y Magia (Doble 100%) restauradas con éxito (Modo Dios desactivado)!")
        return True

    def unlock_all_items(self):
        """Desbloquea los 85 ítems vía HOS_INPUT_LIVE (comandos !cheat n)."""
        def _worker():
            self.log.info("Desbloqueando los 85 ítems del inventario vía HOS_INPUT_LIVE...")
            path = os.path.abspath("hookshot_live_input.txt")
            try:
                open(path, "w", encoding="utf-8").close()
            except Exception:
                pass
            for i in range(85):
                try:
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(f"!cheat {i}\n")
                    time.sleep(0.035)
                except Exception:
                    pass
            self.log.ok("¡Desbloqueo de ítems enviado (85 comandos !cheat)!")
        threading.Thread(target=_worker, daemon=True).start()


# =============================================================================
# INTERFAZ GRÁFICA — DISEÑO TIPO MENÚ DEL JUEGO (SWITCH 2 / OOT)
# =============================================================================
class TriforceModGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = LiveLogger()
        self.ctrl = TriforceModController(self.logger)

        self.root.title("The Legend of Zelda: Ocarina of Time — Triforce Mod Menu")
        self.root.geometry("1280x800")
        self.root.minsize(1080, 720)
        self.root.configure(bg=BG_DEEP)
        Ticker.bind(self.root)

        self.var_topmost = tk.BooleanVar(value=False)
        self.root.attributes("-topmost", False)

        self.var_god_mode = tk.BooleanVar(value=False)
        self.var_inf_health = tk.BooleanVar(value=False)
        self.var_inf_magic = tk.BooleanVar(value=False)
        self.var_no_clip = tk.BooleanVar(value=False)
        self.var_inf_rupees = tk.BooleanVar(value=False)

        self.damage_options = ["x1 Normal", "x2 Doble Daño", "x4 Cuádruple", "x8 Brutal", "💀 One-Hit Kill"]
        self.damage_idx = 0
        self.speed_options = ["1.0x Normal", "1.25x Ágil", "1.5x Rápido", "2.0x Veloz", "3.0x Relámpago"]
        self.speed_idx = 0
        self.game_speed_options = ["0.5x Cámara Lenta", "1.0x Tiempo Real", "1.5x Acelerado", "2.0x Doble Velocidad"]
        self.game_speed_idx = 1
        self.age_options = ["👦 Link Niño", "🧑 Link Adulto"]
        self.age_idx = 1

        self.var_desc_title = tk.StringVar(value="Triforce Mod Menu v4.8")
        self.var_desc_body = tk.StringVar(
            value="Menú de modificaciones externo para The Legend of Zelda: Ocarina of Time.\n\n"
                  "Controla salud, magia, invulnerabilidad, velocidad, inventario y teletransporte "
                  "en caliente mientras juegas, sin interrupciones."
        )
        self.var_desc_note = tk.StringVar(value="Escáner dinámico de la estructura de Link en memoria.")

        self.var_fps_text = tk.StringVar(value="-- FPS")
        self.var_map_text = tk.StringVar(value="Conectando...")
        self.var_age_badge = tk.StringVar(value="ADULTO")
        self.var_toast_msg = tk.StringVar(value="")
        self.var_tp_filter = tk.StringVar(value="")

        self.active_tab_idx = 0
        self.tabs = [
            ("combat",   "Combate & Salud"),
            ("teleport", "Teletransporte"),
            ("items",    "Inventario & Ítems"),
            ("system",   "Sistema & Telemetría"),
        ]

        self._build_interface()

        self.root.bind("<q>", lambda _e: self._cycle_tab(-1))
        self.root.bind("<Q>", lambda _e: self._cycle_tab(-1))
        self.root.bind("<e>", lambda _e: self._cycle_tab(1))
        self.root.bind("<E>", lambda _e: self._cycle_tab(1))
        self.root.bind("<Escape>", lambda _e: self.root.iconify())
        self.root.bind("<F5>", lambda _e: self._toggle_bool(self.var_god_mode, "Modo Dios"))
        self.root.bind("<F6>", lambda _e: self._toggle_bool(self.var_inf_health, "Vida Infinita"))
        self.root.bind("<F7>", lambda _e: self._toggle_bool(self.var_inf_magic, "Magia Infinita"))
        self.root.bind("<F8>", lambda _e: self._toggle_bool(self.var_no_clip, "Vuelo No-Clip"))
        self.root.bind("<F9>", lambda _e: self._toggle_bool(self.var_inf_rupees, "Rupias & Munición"))

        self._start_ui_loop()

    def _build_interface(self):
        # --- BARRA SUPERIOR (estilo menú del juego) ---
        header = tk.Frame(self.root, bg=BG_DEEP, height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        h_left = tk.Frame(header, bg=BG_DEEP)
        h_left.pack(side="left", padx=(16, 0))
        tk.Label(h_left, text="Zelda: Ocarina of Time", bg=BG_DEEP, fg=GOLD, font=F_LOGO).pack(side="left", padx=(0, 10))
        tk.Label(h_left, text="Triforce Menu", bg=BG_DEEP, fg=TEXT, font=F_LOGO).pack(side="left")

        self.tab_container = tk.Frame(header, bg=BG_DEEP)
        self.tab_container.pack(side="left", padx=30)
        self.tab_buttons = []
        for i, (key, label) in enumerate(self.tabs):
            b = tk.Label(self.tab_container, text=label, padx=20, pady=14,
                         bg=BG_DEEP, fg=TEXT_DIM, font=("Georgia", 11, "bold"), cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda _e, idx=i: self._set_active_tab(idx))
            self.tab_buttons.append(b)

        h_right = tk.Frame(header, bg=BG_DEEP)
        h_right.pack(side="right", padx=(0, 20))
        self.btn_pin = tk.Label(h_right, text="📌 Fijar", padx=10, pady=6,
                                bg=CARD, fg=GOLD, font=F_TINY, cursor="hand2",
                                highlightthickness=1, highlightbackground=BORDER)
        self.btn_pin.pack(side="left", padx=(0, 12))
        self.btn_pin.bind("<Button-1>", lambda _e: self._toggle_topmost())
        fps_box = tk.Frame(h_right, bg=BG_DEEP)
        fps_box.pack(side="right")
        tk.Label(fps_box, textvariable=self.var_fps_text, bg=BG_DEEP, fg=GREEN, font=F_DATA).pack(anchor="e")
        tk.Label(fps_box, textvariable=self.var_map_text, bg=BG_DEEP, fg=TEXT_FAINT, font=F_SMALL).pack(anchor="e")

        self.toast_banner = tk.Frame(self.root, bg=BG_DEEP)
        self.lbl_toast = tk.Label(self.toast_banner, textvariable=self.var_toast_msg,
                                  bg=CARD, fg=GOLD_SOFT, font=F_SMALL_B, pady=6)
        self.lbl_toast.pack(fill="x", padx=10, pady=3)

        # --- CUERPO PRINCIPAL: panel izquierdo grande + panel derecho fijo ancho ---
        body = tk.Frame(self.root, bg=BG_DEEP, padx=10, pady=10)
        body.pack(fill="both", expand=True)

        # Columna izquierda: contenido con scroll (ocupa el resto del ancho)
        left_outer = tk.Frame(body, bg=CARD, highlightthickness=2, highlightbackground=BORDER_HARD)
        left_outer.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.canvas = tk.Canvas(left_outer, bg=CARD, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        self.scroll_content = tk.Frame(self.canvas, bg=CARD)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.scroll_content.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.page_frames = {}
        for key, _ in self.tabs:
            p = tk.Frame(self.scroll_content, bg=CARD)
            self.page_frames[key] = p
        self._build_page_combat(self.page_frames["combat"])
        self._build_page_teleport(self.page_frames["teleport"])
        self._build_page_items(self.page_frames["items"])
        self._build_page_system(self.page_frames["system"])

        # Columna derecha: ANCHO FIJO 450px, scroll propio, siempre visible completo
        right_outer = tk.Frame(body, bg=CARD, highlightthickness=2, highlightbackground=BORDER_HARD, width=450)
        right_outer.pack(side="right", fill="y", padx=(8, 0))
        right_outer.pack_propagate(False)

        right_canvas = tk.Canvas(right_outer, bg=CARD, highlightthickness=0, width=440)
        right_canvas.pack(side="left", fill="both", expand=True, padx=3, pady=3)

        right_scrollbar = tk.Scrollbar(right_outer, orient="vertical", command=right_canvas.yview)
        right_scrollbar.pack(side="right", fill="y")
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        right_inner = tk.Frame(right_canvas, bg=CARD)
        right_window = right_canvas.create_window((0, 0), window=right_inner, anchor="nw")
        right_inner.bind("<Configure>", lambda _e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))
        right_canvas.bind("<Configure>", lambda e: right_canvas.itemconfig(right_window, width=440))
        right_canvas.bind_all("<MouseWheel>", lambda e: right_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._build_desc_card(right_inner)
        self._build_hud_card(right_inner)
        self._build_scanner_card(right_inner)
        self._build_quick_actions(right_inner)

        footer = tk.Frame(self.root, bg=BG_DEEP, height=34, padx=18)
        footer.pack(fill="x", side="bottom", pady=(0, 6))
        prompts = [("Pestañas", "Q", "E"), ("Acceso Rápido", "F5-F9"), ("Activar", "Click"), ("Ocultar", "Esc")]
        p_row = tk.Frame(footer, bg=BG_DEEP)
        p_row.pack(side="right")
        for label, *keys in prompts:
            tk.Label(p_row, text=label, bg=BG_DEEP, fg=TEXT_FAINT, font=F_TINY).pack(side="left", padx=(10, 4))
            for k in keys:
                b = tk.Frame(p_row, bg="#ffffff", padx=4, pady=1)
                b.pack(side="left", padx=2)
                tk.Label(b, text=k, bg="#ffffff", fg="#000000", font=F_TINY).pack()

        self._set_active_tab(0)

    def _build_desc_card(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=10, pady=10,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=(0, 8))
        tk.Label(card, textvariable=self.var_desc_title, bg=CARD, fg=TEXT, font=F_UI_B, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(card, textvariable=self.var_desc_body, bg=CARD, fg=TEXT_DIM, font=F_SMALL, justify="left", wraplength=240, anchor="nw").pack(fill="x", pady=(0, 6))
        note_row = tk.Frame(card, bg=CARD)
        note_row.pack(fill="x")
        tk.Label(note_row, text="|", bg=CARD, fg=GOLD, font=F_TINY).pack(side="left", padx=(0, 6))
        tk.Label(note_row, textvariable=self.var_desc_note, bg=CARD, fg=GOLD_SOFT, font=F_TINY, justify="left", wraplength=300).pack(side="left")

    def _build_hud_card(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=10, pady=10,
                        highlightthickness=2, highlightbackground=BORDER_HARD)
        card.pack(fill="x", pady=(0, 8))
        tk.Label(card, text="ESTADO DE LINK EN VIVO", bg=CARD, fg=GOLD, font=("Georgia", 11, "bold")).pack(anchor="w", pady=(0, 10))
        self.lbl_hud_hearts = tk.Label(card, text="❤️ Salud: -- / --", bg=CARD, fg=TEXT, font=("Georgia", 11))
        self.lbl_hud_hearts.pack(anchor="w", pady=2)
        self.lbl_hud_magic = tk.Label(card, text="🔮 Magia: -- / --", bg=CARD, fg=TEXT, font=("Georgia", 11))
        self.lbl_hud_magic.pack(anchor="w", pady=2)
        self.lbl_hud_rupees = tk.Label(card, text="💎 Rupias: --", bg=CARD, fg=RUPEE, font=("Georgia", 11, "bold"))
        self.lbl_hud_rupees.pack(anchor="w", pady=2)
        self.lbl_hud_arrows = tk.Label(card, text="🏹 Flechas: --", bg=CARD, fg=TEXT, font=("Georgia", 11))
        self.lbl_hud_arrows.pack(anchor="w", pady=2)
        self.lbl_hud_god = tk.Label(card, text="🛡️ Modo Dios: Desactivado", bg=CARD, fg=GREEN, font=("Georgia", 10, "bold"))
        self.lbl_hud_god.pack(anchor="w", pady=2)
        self.lbl_hud_engine = tk.Label(card, text="⚙️ Motor: Conectando...", bg=CARD, fg=TEXT_FAINT, font=F_TINY)
        self.lbl_hud_engine.pack(anchor="w", pady=2)

    def _build_scanner_card(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=16, pady=14,
                        highlightthickness=2, highlightbackground=BORDER_HARD)
        card.pack(fill="both", expand=True, pady=(0, 12))
        tk.Label(card, text="ESCÁNER DE MEMORIA — LO QUE TENGO", bg=CARD, fg=GOLD, font=("Georgia", 11, "bold")).pack(anchor="w", pady=(0, 10))

        # Filtros opcionales del usuario para acelerar el escaneo
        filter_frame = tk.Frame(card, bg=ROW, padx=10, pady=8,
                                highlightthickness=1, highlightbackground=BORDER)
        filter_frame.pack(fill="x", pady=(0, 10))
        tk.Label(filter_frame, text="Filtros (lo que tienes ahora):", bg=ROW, fg=TEXT_FAINT, font=("Georgia", 9, "bold")).pack(anchor="w", pady=(0, 4))

        row1 = tk.Frame(filter_frame, bg=ROW)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Rupias:", bg=ROW, fg=TEXT, font=("Georgia", 9, "bold")).pack(side="left", padx=(0, 3))
        self.var_f_rupees = tk.StringVar(value="")
        ent_r = tk.Entry(row1, textvariable=self.var_f_rupees, bg=CARD, fg=TEXT, insertbackground="#ffffff",
                         font=("Consolas", 9), width=8, relief="flat")
        ent_r.pack(side="left", padx=(0, 8))
        tk.Label(row1, text="Flechas:", bg=ROW, fg=TEXT, font=("Georgia", 9, "bold")).pack(side="left", padx=(0, 3))
        self.var_f_arrows = tk.StringVar(value="")
        ent_a = tk.Entry(row1, textvariable=self.var_f_arrows, bg=CARD, fg=TEXT, insertbackground="#ffffff",
                         font=("Consolas", 9), width=8, relief="flat")
        ent_a.pack(side="left", padx=(0, 8))
        tk.Label(row1, text="Corazones:", bg=ROW, fg=TEXT, font=("Georgia", 9, "bold")).pack(side="left", padx=(0, 3))
        self.var_f_hearts = tk.StringVar(value="")
        ent_h = tk.Entry(row1, textvariable=self.var_f_hearts, bg=CARD, fg=TEXT, insertbackground="#ffffff",
                         font=("Consolas", 9), width=8, relief="flat")
        ent_h.pack(side="left", padx=(0, 8))
        tk.Label(row1, text="Bombas:", bg=ROW, fg=TEXT, font=("Georgia", 9, "bold")).pack(side="left", padx=(0, 3))
        self.var_f_bombs = tk.StringVar(value="")
        ent_b = tk.Entry(row1, textvariable=self.var_f_bombs, bg=CARD, fg=TEXT, insertbackground="#ffffff",
                         font=("Consolas", 9), width=8, relief="flat")
        ent_b.pack(side="left")

        self.scanner_box = tk.Frame(card, bg=ROW, highlightthickness=1, highlightbackground=BORDER_SOFT)
        self.scanner_box.pack(fill="both", expand=True)
        self.scanner_rows = {}
        specs = [
            ("heart",  "Salud actual",   "cur_hp",  "—", True),
            ("heart",  "Salud máxima",   "max_hp",  "—", True),
            ("magic",  "Magia actual",   "magic",   "—", True),
            ("coin",   "Rupias",         "rupees",  "—", True),
            ("bolt",   "Flechas",        "arrows",  "—", True),
            ("bomb",   "Bombas",         "bombs",   "—", True),
            ("seed",   "Nueces Deku",    "nuts",    "—", True),
            ("stick",  "Palos Deku",    "sticks",  "—", True),
            ("bean",   "Semillas Mágicas","beans", "—", True),
        ]
        for icon, label, key, value, ok in specs:
            row = ValueRow(self.scanner_box, icon, label, value=value, status="—")
            row.pack(fill="x", pady=2)
            self.scanner_rows[key] = row

        btn_scan = FluidButton(card, "Escanear Memoria Ahora", icon="search",
                               command=self._action_rescan, style="primary", width=320, height=36)
        btn_scan.pack(pady=(10, 0))

        self.lbl_scan_prog = tk.Label(card, text="Listo para escanear", bg=CARD, fg=TEXT_FAINT, font=("Georgia", 9))
        self.lbl_scan_prog.pack(anchor="w", pady=(6, 0))

        # Campo de direccion manual
        addr_frame = tk.Frame(card, bg=ROW, padx=10, pady=8,
                              highlightthickness=1, highlightbackground=BORDER)
        addr_frame.pack(fill="x", pady=(12, 0))
        tk.Label(addr_frame, text="Direccion manual de Link:", bg=ROW, fg=TEXT_FAINT, font=("Georgia", 9, "bold")).pack(side="left", padx=(0, 8))
        self.var_manual_addr = tk.StringVar(value="0x101002410CA8")
        ent_addr = tk.Entry(addr_frame, textvariable=self.var_manual_addr, bg=CARD, fg=TEXT, insertbackground="#ffffff",
                            font=("Consolas", 9), width=20, relief="flat")
        ent_addr.pack(side="left", padx=(0, 8))
        btn_addr = FluidButton(addr_frame, "Establecer", command=self._action_set_manual_addr,
                               style="secondary", width=90, height=30)
        btn_addr.pack(side="left")

    def _action_set_manual_addr(self):
        raw = self.var_manual_addr.get().strip()
        try:
            addr = int(raw, 16) if raw.lower().startswith("0x") else int(raw)
            ok = self.ctrl.mem._is_valid_player_struct(addr)
            if ok:
                self.ctrl.mem.struct_verified = True
                self.ctrl.mem._warned_title_screen = False
                self._show_toast(f"✅ Dirección establecida: 0x{addr:X}")
                self.logger.ok(f"Direccion manual de Link establecida: 0x{addr:X}")
            else:
                self._show_toast("⚠️ Direccion invalida: no se encontro estructura de Link ahi")
                self.logger.warn(f"Direccion manual invalida: 0x{addr:X}")
        except Exception as e:
            self._show_toast("⚠️ Formato invalido (usa 0x101002410CA8)")
            self.logger.err(f"Error al establecer direccion manual: {e}")

    def _build_quick_actions(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=16, pady=14,
                        highlightthickness=2, highlightbackground=BORDER_HARD)
        card.pack(fill="x", pady=(0, 12))
        tk.Label(card, text="ACCIONES RÁPIDAS", bg=CARD, fg=GOLD, font=("Georgia", 11, "bold")).pack(anchor="w", pady=(0, 10))
        btn_god = FluidButton(card, "🛡️ Alternar Modo Dios (F5)", icon="heart",
                              command=lambda: self._toggle_bool(self.var_god_mode, "Modo Dios"), style="primary", width=320, height=36)
        btn_god.pack(fill="x", pady=4)
        btn_magic = FluidButton(card, "🔮 Alternar Magia Infinita (F7)", icon="bolt",
                                command=lambda: self._toggle_bool(self.var_inf_magic, "Magia Infinita"), style="secondary", width=320, height=36)
        btn_magic.pack(fill="x", pady=4)
        btn_items = FluidButton(card, "⭐ Desbloquear Todos los Ítems", icon="chest",
                                command=self._action_unlock_all, style="secondary", width=320, height=36)
        btn_items.pack(fill="x", pady=4)
        btn_warp = FluidButton(card, "🌿 Teletransporte a Bosque Kokiri", icon="pin",
                               command=lambda: self._execute_warp(0, "Bosque Kokiri"), style="secondary", width=320, height=36)
        btn_warp.pack(fill="x", pady=4)

    def _toggle_topmost(self):
        new_val = not self.var_topmost.get()
        self.var_topmost.set(new_val)
        self.root.attributes("-topmost", new_val)
        if new_val:
            self.btn_pin.configure(bg=CARD, fg="#ffffff", text="📌 Fijado")
            self._show_toast("📌 Ventana fijada en primer plano")
        else:
            self.btn_pin.configure(bg=PANEL, fg=TEXT_FAINT, text="📌 Fijar")
            self._show_toast("📌 Modo superpuesto desactivado")

    def _sync_cheats(self):
        self.ctrl.god_mode = self.var_god_mode.get()
        self.ctrl.inf_health = self.var_inf_health.get()
        self.ctrl.inf_magic = self.var_inf_magic.get()
        self.ctrl.no_clip_flight = self.var_no_clip.get()
        self.ctrl.inf_rupees_ammo = self.var_inf_rupees.get()
        if self.ctrl.inf_magic:
            self.ctrl.apply_instant_magic_refill()
        self.ctrl.apply_instant_god_mode(self.ctrl.god_mode)

    def _toggle_bool(self, var: tk.BooleanVar, label):
        val = not var.get()
        var.set(val)
        self._sync_cheats()
        state_txt = "ACTIVADO" if val else "DESACTIVADO"
        self._show_toast(f"⚡ [{label}]: {state_txt}")

    def _set_damage_idx(self, idx):
        self.damage_idx = idx
        mults = [1.0, 2.0, 4.0, 8.0, 255.0]
        self.ctrl.damage_mult = mults[idx]
        try:
            self.ctrl.bridge.set_option("damage_multiplier", int(mults[idx]))
        except Exception:
            pass
        self._show_toast(f"⚔️ Daño fijado en {self.damage_options[idx]}")

    def _set_speed_idx(self, idx):
        self.speed_idx = idx
        self.ctrl.link_speed_idx = idx
        self._show_toast(f"🏃 Velocidad fijada en {self.speed_options[idx]}")

    def _set_game_speed_idx(self, idx):
        self.game_speed_idx = idx
        val = 0 if idx == 0 else 1
        self.ctrl.bridge.set_option("game_speed", val)
        self._show_toast(f"⏱️ Simulación: {self.game_speed_options[idx]}")

    def _set_age_idx(self, idx):
        self.age_idx = idx
        target = "child" if idx == 0 else "adult"
        ok, msg = self.ctrl.bridge.set_age(target)
        self._show_toast(f"⌛ {msg}")

    def _show_toast(self, message):
        self.var_toast_msg.set(message)
        self.toast_banner.pack(fill="x", side="top", pady=(0, 4))
        self.lbl_toast.pack(fill="x")
        self.root.after(4000, lambda: self.toast_banner.pack_forget())

    def _action_unlock_all(self):
        self.ctrl.unlock_all_items()
        self._show_toast("⭐ ¡Todos los ítems desbloqueados (85 comandos)!")

    def _action_rescan(self):
        rup = self.var_f_rupees.get().strip()
        arr = self.var_f_arrows.get().strip()
        hrt = self.var_f_hearts.get().strip()
        bmb = getattr(self, "var_f_bombs", tk.StringVar()).get().strip()
        filt_rup = int(rup) if rup.isdigit() else None
        filt_arr = int(arr) if arr.isdigit() else None
        filt_hrt = int(hrt) if hrt.isdigit() else None
        filt_bmb = int(bmb) if bmb.isdigit() else None

        self.lbl_scan_prog.configure(text="Escaneando memoria por bloques...", fg=GOLD)
        self._show_toast("🔍 Escaneando memoria del motor...")
        threading.Thread(target=self._rescan_worker, args=(filt_rup, filt_hrt, filt_arr, filt_bmb), daemon=True).start()

    def _rescan_worker(self, known_rupees=None, known_hearts=None, known_arrows=None, known_bombs=None):
        ok = self.ctrl.mem.scan_coordinated_block(known_rupees=known_rupees, known_hearts=known_hearts, known_arrows=known_arrows, known_bombs=known_bombs)
        def _update():
            if ok:
                self.lbl_scan_prog.configure(text="✅ Estructura de Link sincronizada en vivo", fg=GREEN)
                self._show_toast("✅ Escaneo exitoso. Inventario y salud sincronizados.")
                self.logger.ok("Escaneo completado con éxito.")
            else:
                self.lbl_scan_prog.configure(text="⚠️ No se encontró. Prueba ingresando tus valores actuales.", fg=RED)
                self._show_toast("⚠️ No se encontró la estructura con esos filtros.")
                self.logger.warn("Escaneo: estructura no encontrada.")
        self.root.after(0, _update)

    def _action_relaunch_admin(self):
        if not sys.platform.startswith("win"):
            return
        try:
            script_path = os.path.abspath(__file__)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}" --elevated', None, 1)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo elevar privilegios: {e}")

    def _append_log(self, level, line):
        pass

    def _start_ui_loop(self):
        def _tick():
            fps = self.ctrl.live_fps
            scene = self.ctrl.live_map
            age = self.ctrl.live_age
            self.var_fps_text.set(f"{fps:.1f} FPS" if fps > 0 else "-- FPS")
            self.var_map_text.set(scene if scene else "Conectando...")
            self.var_age_badge.set(age)
            god_on = self.var_god_mode.get()
            self.lbl_hud_god.configure(text=f"🛡️ Modo Dios: {'ACTIVO (Invulnerable)' if god_on else 'Desactivado'}", fg=GREEN if god_on else TEXT)

            mem = self.ctrl.mem
            if not mem.is_attached():
                self.lbl_hud_engine.configure(text="⚙️ Motor: Desconectado (ejecuta hookshot.exe)", fg=RED)
            elif not mem.struct_verified:
                self.lbl_hud_engine.configure(text="⚙️ Motor: Conectado - Buscando estructura de Link...", fg="#f0b429")
            else:
                vk = mem.player_struct_addr or 0
                self.lbl_hud_engine.configure(text=f"⚙️ Motor: Conectado - Link localizado (0x{vk:X})", fg=GREEN)

            ch, mh = self.ctrl.live_cur_hp, self.ctrl.live_max_hp
            self.lbl_hud_hearts.configure(text=f"❤️ Salud: {ch//4 if ch else 20} / {mh//4 if mh else 20} corazones")
            self.lbl_hud_magic.configure(text=f"🔮 Magia: {self.ctrl.live_magic} / 96")
            self.lbl_hud_rupees.configure(text=f"💎 Rupias: {self.ctrl.live_rupees}")
            self.lbl_hud_arrows.configure(text=f"🏹 Flechas: {self.ctrl.live_arrows}")
            self._update_scanner_rows()
            self.root.after(300, _tick)
        self.root.after(300, _tick)

    def _update_scanner_rows(self):
        c = self.ctrl
        values = {
            "cur_hp": (f"{c.live_cur_hp//4} corazones" if c.live_cur_hp else "20 corazones", True),
            "max_hp": (f"{c.live_max_hp//4} corazones" if c.live_max_hp else "20 corazones", True),
            "magic":  (f"{c.live_magic} / 96", True),
            "rupees": (f"{c.live_rupees}", True),
            "arrows": (f"{c.live_arrows}", True),
            "bombs":  (f"{c.live_bombs}", True),
            "nuts":   (f"{c.live_nuts}", True),
            "sticks": (f"{c.live_sticks}", True),
            "beans":  (f"{c.live_beans}", True),
        }
        for key, (val, ok) in values.items():
            row = self.scanner_rows.get(key)
            if row:
                row.set_value(val, ok)
        for key, (val, ok) in values.items():
            row = self.scanner_rows.get(key)
            if row:
                row.set_value(val, ok)

    # ---------------------------------------------------------------------
    # PÁGINA 1: COMBATE & SALUD
    # ---------------------------------------------------------------------
    def _build_page_combat(self, parent):
        SectionLabel(parent, "Salud, Invencibilidad y Magia").pack(fill="x", pady=(0, 6))

        def _mk_toggle(var, label, title, body, note):
            r = HoverRow(parent, on_hover=lambda: self._set_desc(title, body, note))
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=ROW, fg=TEXT, font=F_UI_B).pack(side="left")
            seg = tk.Frame(r, bg=ROW)
            seg.pack(side="right")
            off_lbl = tk.Label(seg, text="Desactivado", padx=12, pady=4, font=F_TINY, cursor="hand2", bg=ROW, fg=TEXT_FAINT)
            off_lbl.pack(side="left", padx=1)
            on_lbl = tk.Label(seg, text="Activado", padx=12, pady=4, font=F_TINY, cursor="hand2", bg=ROW, fg=TEXT_FAINT)
            on_lbl.pack(side="left", padx=1)
            def _update():
                on = var.get()
                if on:
                    on_lbl.configure(bg=PILL_ON if hasattr(__import__('ztk'), 'PILL_ON') else GOLD_DIM, fg=TEXT)
                    off_lbl.configure(bg=PILL_OFF if hasattr(__import__('ztk'), 'PILL_OFF') else ROW_ACTIVE, fg=TEXT_MUTED if hasattr(__import__('ztk'), 'TEXT_MUTED') else TEXT_FAINT)
                    r.configure(highlightbackground=GOLD, highlightthickness=2)
                else:
                    on_lbl.configure(bg=ROW_ACTIVE, fg=TEXT_MUTED if hasattr(__import__('ztk'), 'TEXT_MUTED') else TEXT_FAINT)
                    off_lbl.configure(bg="#1c140e", fg=TEXT)
                    r.configure(highlightbackground=BORDER_SOFT, highlightthickness=1)
            def _set(v):
                var.set(v); self._sync_cheats(); _update()
                self._show_toast(f"⚡ {label}: {'Activado' if v else 'Desactivado'}")
            off_lbl.bind("<Button-1>", lambda _e: _set(False))
            on_lbl.bind("<Button-1>", lambda _e: _set(True))
            def _enter(_e):
                r.configure(bg=ROW_HOVER)
                for w in (r, seg, off_lbl, on_lbl):
                    try: w.configure(bg=ROW_HOVER)
                    except: pass
            def _leave(_e):
                r.configure(bg=ROW)
                for w in (r, seg, off_lbl, on_lbl):
                    try: w.configure(bg=ROW)
                    except: pass
            for w in (r, seg, off_lbl, on_lbl):
                w.bind("<Enter>", _enter); w.bind("<Leave>", _leave)
            _update()
            return r

        _mk_toggle(self.var_inf_health, "Vida Infinita (20 Corazones)", "Vida Infinita",
                   "Mantiene los 20 corazones llenos permanentemente y congela el daño en caliente.",
                   "Acceso rápido: [F6]. Congela el medidor de salud.")
        _mk_toggle(self.var_inf_magic, "Magia Infinita (Barra Doble)", "Magia Infinita",
                   "Rellena la barra verde de magia doble al 100% y bloquea el consumo de hechizos mágicos.",
                   "Acceso rápido: [F7]. Hechizos ilimitados.")
        _mk_toggle(self.var_god_mode, "Modo Dios / Invulnerabilidad Total", "Modo Dios",
                   "Activa la protección nativa del motor de Hookshot. Link no sufre daño de ningún enemigo, "
                   "trampa, proyectil, caída al vacío ni lava.",
                   "Acceso rápido: [F5]. Protección total en tiempo real.")

        SectionLabel(parent, "Físicas, Combate y Movimiento").pack(fill="x", pady=(16, 6))

        def _mk_stepper(label, options, get_idx, set_idx, title, body, note):
            r = HoverRow(parent, on_hover=lambda: self._set_desc(title, body, note))
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=ROW, fg=TEXT, font=F_UI_B).pack(side="left")
            st = Stepper(r, options, get_idx, set_idx, bg=ROW, width=210)
            st.pack(side="right")
            return r

        _mk_stepper("Multiplicador de Daño de Link", self.damage_options,
                    lambda: self.damage_idx, self._set_damage_idx,
                    "Multiplicador de Daño de Espada",
                    "Multiplica la fuerza del corte de la espada de Link. De daño normal x1 a muerte instantánea de un golpe.",
                    "Afecta a Espada Kokiri, Espada Maestra y Biggoron.")
        _mk_stepper("Velocidad de Movimiento de Link", self.speed_options,
                    lambda: self.speed_idx, self._set_speed_idx,
                    "Velocidad de Desplazamiento",
                    "Modifica la velocidad a la que Link camina, corre, trepa y nada por Hyrule.",
                    "Ajustable de 1.0x hasta 3.0x Relámpago.")

        _mk_toggle(self.var_no_clip, "Modo Vuelo Libre (No-Clip)", "Vuelo Libre y Traspaso de Muros",
                   "Permite volar por el aire realizando un doble salto. Atraviesa cualquier muro o colisión.",
                   "Acceso rápido: [F8]. Pulsa Salto dos veces para despegar.")
        _mk_toggle(self.var_inf_rupees, "Rupias (9999) y Munición Infinita (99)", "Rupias y Munición Ilimitada",
                   "Mantiene las rupias en 9999 y congela flechas, bombas, bombchus, semillas, nueces y judías mágicas en 99 unidades.",
                   "Acceso rápido: [F9]. Reservas completas al máximo.")

        SectionLabel(parent, "Simulación del Tiempo y Edad").pack(fill="x", pady=(16, 6))
        _mk_stepper("Velocidad del Juego (Game Speed)", self.game_speed_options,
                    lambda: self.game_speed_idx, self._set_game_speed_idx,
                    "Velocidad Global del Juego",
                    "Controla la velocidad del tiempo del motor. Útil para cámara lenta o acelerar diálogos.",
                    "Se aplica en caliente a través del pipe de Hookshot.")
        _mk_stepper("Transformación de Edad de Link", self.age_options,
                    lambda: self.age_idx, self._set_age_idx,
                    "Alternar entre Link Niño y Adulto",
                    "Cambia instantáneamente la edad de Link y recarga la escena sin viajar al Templo del Tiempo.",
                    "Cambio de edad nativo de Hookshot.")

    # ---------------------------------------------------------------------
    # PÁGINA 2: TELETRANSPORTE
    # ---------------------------------------------------------------------
    def _build_page_teleport(self, parent):
        SectionLabel(parent, "Buscador Rápido de Destinos").pack(fill="x", pady=(0, 6))
        search_box = tk.Frame(parent, bg=ROW, padx=12, pady=6)
        search_box.pack(fill="x", pady=(0, 10))
        tk.Label(search_box, text="🔍 Buscar:", bg=ROW, fg=GOLD_SOFT, font=F_UI_B).pack(side="left", padx=(0, 8))
        entry = tk.Entry(search_box, textvariable=self.var_tp_filter, bg=CARD, fg=TEXT, insertbackground="#ffffff",
                         font=F_UI, relief="flat")
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda _e: self._filter_teleports())

        self.tp_list_frame = tk.Frame(parent, bg=PANEL)
        self.tp_list_frame.pack(fill="both", expand=True)
        self._render_teleport_list()

    def _render_teleport_list(self, filter_text=""):
        for w in self.tp_list_frame.winfo_children():
            w.destroy()
        categories = ["Ciudades y Aldeas", "Afueras de Templos", "Regiones y Ciudades", "Interiores"]
        query = filter_text.strip().lower()
        for cat in categories:
            matching = [d for d in TELEPORT_LOCATIONS if d["cat"] == cat and
                        (query in d["name"].lower() or query in d["map"].lower())]
            if not matching:
                continue
            SectionLabel(self.tp_list_frame, cat).pack(fill="x", pady=(10, 4))
            for dest in matching:
                self._create_teleport_row(self.tp_list_frame, dest)

    def _create_teleport_row(self, parent, dest):
        row = HoverRow(parent, on_hover=lambda: self._set_desc(dest["name"],
                        f"Viaja a {dest['name']} ({dest['map']}).",
                        f"Mapa interno del motor: {dest['map']}"))
        row.pack(fill="x", pady=2)
        info = tk.Frame(row, bg=ROW)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=dest["name"], bg=ROW, fg=TEXT, font=F_UI_B).pack(anchor="w")
        tk.Label(info, text=dest["map"], bg=ROW, fg=TEXT_FAINT, font=F_SMALL).pack(anchor="w")
        btn = tk.Label(row, text="VIAJAR AHORA", padx=10, pady=4, bg=GOLD_DIM, fg=TEXT,
                       font=F_TINY, cursor="hand2")
        btn.pack(side="right")
        btn.bind("<Button-1>", lambda _e, idx=dest["idx"], name=dest["name"]: self._execute_warp(idx, name))
        def _enter(_e):
            row.configure(bg=ROW_HOVER)
            for w in (row, info): w.configure(bg=ROW_HOVER)
            btn.configure(bg=GOLD_SOFT)
        def _leave(_e):
            row.configure(bg=ROW)
            for w in (row, info): w.configure(bg=ROW)
            btn.configure(bg=GOLD_DIM)
        for w in (row, info):
            w.bind("<Enter>", _enter); w.bind("<Leave>", _leave)

    def _filter_teleports(self):
        self._render_teleport_list(self.var_tp_filter.get())

    def _execute_warp(self, idx, name):
        self._show_toast(f"⚡ Viajando hacia {name}...")
        threading.Thread(target=self._warp_worker, args=(idx, name), daemon=True).start()

    def _warp_worker(self, idx, name):
        ok, msg = self.ctrl.bridge.teleport(idx)
        if ok:
            self._show_toast(f"✨ ¡Llegada con éxito a {name}!")
            self.logger.ok(f"Teletransporte completado: {name} (idx {idx})")
        else:
            self._show_toast(f"⚠️ {msg}")
            self.logger.warn(f"Error en teletransporte: {msg}")

    # ---------------------------------------------------------------------
    # PÁGINA 3: INVENTARIO & ÍTEMS
    # ---------------------------------------------------------------------
    def _build_page_items(self, parent):
        SectionLabel(parent, "Gestor Rápido de Inventario").pack(fill="x", pady=(0, 6))

        r2 = HoverRow(parent, on_hover=lambda: self._set_desc(
            "Desbloqueo Maestro de Inventario",
            "Otorga todas las espadas, escudos, túnicas, botas, botellas, medallones de sabios, "
            "canciones de ocarina y 100 símbolos de Skulltula dorada.",
            "Desbloqueo permanente para esta sesión."))
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text="Desbloquear Todos los Ítems y Equipamiento", bg=ROW, fg=TEXT, font=F_UI_B).pack(side="left")
        FluidButton(r2, "DESBLOQUEAR TODO", command=self._action_unlock_all, style="secondary", width=140, height=32).pack(side="right")

    # ---------------------------------------------------------------------
    # PÁGINA 4: SISTEMA & TELEMETRÍA
    # ---------------------------------------------------------------------
    def _build_page_system(self, parent):
        SectionLabel(parent, "Diagnóstico en Vivo del Motor").pack(fill="x", pady=(0, 6))

        r = HoverRow(parent, on_hover=lambda: self._set_desc(
            "Calibración de Punteros de Memoria",
            "Inspecciona la memoria en tiempo real para encontrar la estructura de Link y calibrar cheats.",
            "Optimizado para Windows 64-bit."))
        r.pack(fill="x", pady=2)
        tk.Label(r, text="Re-escanear Memoria y Punteros de Link", bg=ROW, fg=TEXT, font=F_UI_B).pack(side="left")
        FluidButton(r, "ESCANEAR AHORA", command=self._action_rescan, style="primary", width=140, height=32).pack(side="right")

        r2 = HoverRow(parent, on_hover=lambda: self._set_desc(
            "Elevación UAC de Windows",
            "Si el juego se ejecuta como Administrador, el Mod Menu requiere elevación UAC para escribir en la memoria.",
            "Reinicia la aplicación con elevación Win32."))
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text="Reiniciar Mod Menu con permisos de Administrador", bg=ROW, fg=TEXT, font=F_UI_B).pack(side="left")
        FluidButton(r2, "ELEVAR ADMIN", command=self._action_relaunch_admin, style="secondary", width=150, height=32).pack(side="right")

        SectionLabel(parent, "Consola de Diagnóstico (triforce_modmenu_debug.log)").pack(fill="x", pady=(16, 6))
        log_box = tk.Frame(parent, bg="#0a0b10", padx=8, pady=8)
        log_box.pack(fill="both", expand=True)
        self.txt_log = tk.Text(log_box, bg="#0a0b10", fg="#c4b5a5", insertbackground="#ffffff",
                               font=("Consolas", 8), height=14, relief="flat", wrap="none")
        self.txt_log.pack(fill="both", expand=True)
        self.logger.add_listener(self._append_log)
        self.logger.info("Triforce Engine v4.8 listo y activo.")

    # ---------------------------------------------------------------------
    # NAVEGACIÓN DE PESTAÑAS
    # ---------------------------------------------------------------------
    def _set_active_tab(self, idx):
        self.active_tab_idx = idx
        for i, b in enumerate(self.tab_buttons):
            if i == idx:
                b.configure(bg=CARD, fg=GOLD_SOFT)
            else:
                b.configure(bg=PANEL, fg=TEXT_FAINT)
        target_key = self.tabs[idx][0]
        for k, p in self.page_frames.items():
            if k == target_key:
                p.pack(fill="both", expand=True)
            else:
                p.pack_forget()
        self.canvas.yview_moveto(0)

    def _cycle_tab(self, direction):
        new_idx = (self.active_tab_idx + direction) % len(self.tabs)
        self._set_active_tab(new_idx)

    def _set_desc(self, title, body, note="Se sincroniza en caliente sin reiniciar."):
        self.var_desc_title.set(title)
        self.var_desc_body.set(body)
        self.var_desc_note.set(note)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
def ensure_windows_admin():
    if not sys.platform.startswith("win"):
        return
    if "--elevated" in sys.argv:
        return
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            script_path = os.path.abspath(__file__)
            res = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}" --elevated', None, 1)
            if int(res) > 32:
                sys.exit(0)
    except Exception:
        pass


def main():
    skip_admin = "--no-admin" in sys.argv or "--elevated" in sys.argv
    if not skip_admin:
        ensure_windows_admin()
    try:
        root = tk.Tk()
        app = TriforceModGUI(root)
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")


if __name__ == "__main__":
    main()



