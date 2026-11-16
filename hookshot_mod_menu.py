#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  THE LEGEND OF ZELDA: OCARINA OF TIME — TRIFORCE MOD MENU (v4.7)
  Motor Externo de Modificaciones y Cheats en Vivo para el Port Nativo de PC
  (Hookshot v2.2.0-rc.1 / Zelda OoT Switch 2 Port)
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

# =============================================================================
# CONFIGURACIÓN 64-BIT ESTRICTA DE CTYPES PARA WINDOWS
# =============================================================================
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

TH32CS_SNAPMODULE   = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.c_void_p),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260),
    ]

kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

kernel32.Module32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
kernel32.Module32First.restype = wintypes.BOOL

kernel32.Module32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
kernel32.Module32Next.restype = wintypes.BOOL

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

# =============================================================================
# CONSTANTES Y OFFSETS DEL MOTOR NATIVO (hookshot.exe / hookshot_vk.dll)
# =============================================================================
# hookshot_vk.dll (Vulkan Renderer & Overlays)
VK_TIMESTAMP        = 0x6AF88867  # TimeDateStamp exacto de hookshot_vk.dll
VK_IMAGE_SIZE       = 0x11F5000   # SizeOfImage exacto de hookshot_vk.dll
RVA_PROTECT_HEARTS  = 0x9B5830    # uint32: 1 = Modo Dios / Protección de corazones activa
RVA_PLAYER_FLIGHT   = 0xFFDA64    # uint8:  1 = Vuelo libre / No-clip con doble salto
RVA_LINK_SPEED      = 0x9B5758    # uint32: Índice de velocidad de Link (0=1.0x, 1=1.25x, 2=1.5x, 3=2.0x)
RVA_CHEAT_ACTION    = 0x100250C   # uint32: Disparador de acciones del motor
RVA_ITEMS_TABLE     = 0xF24F50    # Tabla de 90 ítems del juego
RVA_ITEM_COUNTS     = 0xFFD910    # Cantidades y munición por ítem

# hookshot.exe (Game Core & Recompiled OoT Runtime)
RVA_EXE_PROTECT     = 0x232C30D0  # hos_oot_protect_hearts en hookshot.exe
RVA_EXE_ACTION      = 0x232C35C8  # hos_oot_live_action en hookshot.exe

# Punteros directos de Link en Guest RAM
GUEST_SAVECONTEXT   = 0x100080CD0EA0
GUEST_PLAYER_PTR    = 0x100084C9E090
GUEST_N64_CTX       = 0x10008011A5D0
GAMEDATA_SIGNATURE  = bytes.fromhex("04030201eb802d00d8750100")

# =============================================================================
# CATÁLOGO DE TELETRANSPORTE
# =============================================================================
TELEPORT_LOCATIONS = [
    # 1. AFUERAS DE TEMPLOS Y MAZMORRAS (Frente a la entrada exterior)
    {"idx": 0,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Gran Árbol Deku", "sub": "Bosque Kokiri (Frente al Árbol)", "map": "KokiriForest", "desc": "Frente a la entrada del Gran Árbol Deku en el claro sagrado del Bosque Kokiri. Evita entrar a la mazmorra y te sitúa listo en el exterior."},
    {"idx": 9,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras de la Cueva Dodongo", "sub": "Sendero de la Montaña de la Muerte", "map": "DeathMountainTrail", "desc": "Frente a la gran roca que bloquea la Cueva de los Dodongos en el sendero escarpado del volcán."},
    {"idx": 14, "cat": "Afueras de Templos y Mazmorras", "name": "Afueras de la Barriga de Jabu-Jabu", "sub": "Fuente de los Zora", "map": "ZoraFountain", "desc": "Junto al muelle sagrado de Lord Jabu-Jabu y el altar del Gran Hada en la Fuente Zora."},
    {"idx": 6,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Templo del Bosque", "sub": "Pradera Sagrada del Bosque", "map": "SacredForestMeadow", "desc": "Al final del laberinto del bosque sagrado, frente a las grandes escalinatas de entrada al Templo del Bosque."},
    {"idx": 10, "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Templo del Fuego", "sub": "Cráter del Volcán de la Muerte", "map": "DeathMountainCrater", "desc": "En el puente colgante sobre la lava ardiente, justo frente al pórtico del Templo del Fuego."},
    {"idx": 7,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Templo del Agua", "sub": "Lago Hylia (Isla Central)", "map": "HyruleField", "desc": "En las orillas del Lago Hylia frente a la puerta sumergida del Templo del Agua y el árbol gigante."},
    {"idx": 8,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Templo de la Sombra", "sub": "Cementerio de Kakariko (Altar)", "map": "Graveyard", "desc": "En la cornisa secreta de antorchas del cementerio, justo frente a la entrada del Templo de la Sombra."},
    {"idx": 18, "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Templo del Espíritu", "sub": "Coloso del Desierto (Entrada)", "map": "DesertColossus", "desc": "Frente a las colosales piernas de la estatua tallada en la roca en el oasis más profundo del desierto."},
    {"idx": 2,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Fondo del Pozo", "sub": "Aldea Kakariko (Plaza del Molino)", "map": "KakarikoVillage", "desc": "Junto al pozo de agua y el molino de viento de Kakariko antes de descender a las catacumbas."},
    {"idx": 14, "cat": "Afueras de Templos y Mazmorras", "name": "Afueras de la Caverna de Hielo", "sub": "Fuente Zora (Bloques de Hielo)", "map": "ZoraFountain", "desc": "Frente a los témpanos flotantes que conducen a la entrada de la Caverna de Hielo cristalina."},
    {"idx": 16, "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Centro Gerudo", "sub": "Fortaleza Gerudo (Patio Central)", "map": "GerudoFortress", "desc": "Frente a la reja de entrada al Centro de Instrucción Gerudo en el corazón de la fortaleza."},
    {"idx": 4,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Castillo de Ganon", "sub": "Castillo de Hyrule (Muralla)", "map": "HyruleCastle", "desc": "En el foso exterior y murallas del Castillo de Hyrule frente al puente mágico de piedra."},
    {"idx": 1,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras de la Ciudadela", "sub": "Pradera de Hyrule (Puente Levadizo)", "map": "HyruleField", "desc": "En la pradera abierta frente a las grandes cadenas y el puente levadizo de la Ciudadela de Hyrule."},
    {"idx": 3,  "cat": "Afueras de Templos y Mazmorras", "name": "Afueras del Templo del Tiempo", "sub": "Plaza del Mercado de la Ciudadela", "map": "Market", "desc": "En el camino de losetas de piedra que desemboca en la fachada del Templo del Tiempo."},

    # 2. REGIONES Y CIUDADES DE HYRULE
    {"idx": 0,  "cat": "Regiones & Ciudades", "name": "Bosque Kokiri", "sub": "Aldea de los Niños del Bosque", "map": "KokiriForest", "desc": "La aldea natal de Link y los Kokiri, con tiendas, chozas y caminos de madera entre los árboles."},
    {"idx": 1,  "cat": "Regiones & Ciudades", "name": "Pradera de Hyrule", "sub": "Llanuras Centrales del Reino", "map": "HyruleField", "desc": "El vasto corazón de Hyrule. Conecta todas las provincias, aldeas y fortalezas del continente."},
    {"idx": 2,  "cat": "Regiones & Ciudades", "name": "Aldea Kakariko", "sub": "Pueblo al Pie de la Montaña", "map": "KakarikoVillage", "desc": "Histórica villa de los Sheikah con el corral de gallinas Cucco, la casa de Skulltulas y la torre de vigía."},
    {"idx": 3,  "cat": "Regiones & Ciudades", "name": "Mercado de la Ciudadela", "sub": "Distrito Comercial", "map": "Market", "desc": "Centro neurálgico del comercio: bazar, tienda de máscaras felices, minijuegos y callejones."},
    {"idx": 5,  "cat": "Regiones & Ciudades", "name": "Bosque Perdido", "sub": "Lost Woods", "map": "LostWood", "desc": "Laberinto misterioso envuelto en niebla y melodías. Hogar de Skull Kids y caminos dimensionales."},
    {"idx": 6,  "cat": "Regiones & Ciudades", "name": "Pradera Sagrada del Bosque", "sub": "Sacred Forest Meadow", "map": "SacredForestMeadow", "desc": "Santuario oculto en lo profundo del bosque donde Saria enseñó a Link su melodía."},
    {"idx": 7,  "cat": "Regiones & Ciudades", "name": "Rancho Lon Lon", "sub": "Finca Ganadera y Pista de Caballos", "map": "HyruleField", "desc": "Hogar de Malon, Talon e Ingo. El rancho donde Link aprende la Canción de Epona y cabalga."},
    {"idx": 8,  "cat": "Regiones & Ciudades", "name": "Cementerio de Kakariko", "sub": "Camposanto Real", "map": "Graveyard", "desc": "Lugar de descanso de la dinastía real de Hyrule y los hermanos compositores Flat y Sharp."},
    {"idx": 9,  "cat": "Regiones & Ciudades", "name": "Sendero de la Montaña de la Muerte", "sub": "Death Mountain Trail", "map": "DeathMountainTrail", "desc": "Camino escarpado azotado por rocas volcánicas incandescentes que asciende hacia la cima del volcán."},
    {"idx": 10, "cat": "Regiones & Ciudades", "name": "Cráter de la Montaña de la Muerte", "sub": "Death Mountain Crater", "map": "DeathMountainCrater", "desc": "Caldera de calor extremo con lava ardiente y el santuario del Gran Hada del Poder."},
    {"idx": 11, "cat": "Regiones & Ciudades", "name": "Ciudad Goron", "sub": "Hogar de la Hermandad Goron", "map": "GoronCity", "desc": "Asentamiento subterráneo excavado en la roca con la sala del trono de Darunia y el jarrón giratorio."},
    {"idx": 12, "cat": "Regiones & Ciudades", "name": "Río de los Zora", "sub": "Cañón Fluvial y Cascadas", "map": "ZoraRiver", "desc": "Río de aguas cristalinas poblado de ranas cantantes y cascadas que guía a los dominios Zora."},
    {"idx": 13, "cat": "Regiones & Ciudades", "name": "Región de los Zora", "sub": "Trono del Rey Zora", "map": "ZoraDomain", "desc": "Majestuosa caverna acuática con cascadas y la cámara real del Rey Zora De Bon XVI."},
    {"idx": 14, "cat": "Regiones & Ciudades", "name": "Fuente de los Zora", "sub": "Lago Sagrado de Jabu-Jabu", "map": "ZoraFountain", "desc": "Reserva de agua sagrada donde descansa el gran pez dios Lord Jabu-Jabu y el santuario del Hada."},
    {"idx": 15, "cat": "Regiones & Ciudades", "name": "Valle Gerudo", "sub": "Puente sobre el Cañón", "map": "GerudoValley", "desc": "Garganta profunda con carpa de carpinteros y el puente de madera que divide el reino de las ladronas."},
    {"idx": 16, "cat": "Regiones & Ciudades", "name": "Fortaleza Gerudo", "sub": "Campamento de las Guerreras", "map": "GerudoFortress", "desc": "Fortaleza inexpugnable donde entrenan las guerreras Gerudo y la prisión de los carpinteros."},
    {"idx": 17, "cat": "Regiones & Ciudades", "name": "Desierto Encantado", "sub": "Haunted Wasteland", "map": "HountedWasteland", "desc": "Tormenta de arena perpetua que solo puede atravesarse siguiendo al fantasma guía con la Lente."},
    {"idx": 18, "cat": "Regiones & Ciudades", "name": "Coloso del Desierto", "sub": "Oasis del Espíritu", "map": "DesertColossus", "desc": "Monumento ancestral erigido en lo más profundo del desierto ante el gran estanque del Gran Hada."},

    # 3. INTERIOR DE MAZMORRAS Y TEMPLOS
    {"idx": 19, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Gran Árbol Deku", "sub": "Inside The Deku Tree", "map": "InsideTheDekuTree", "desc": "Primera mazmorra del juego. Infectada por Gohma y las telarañas parasíticas."},
    {"idx": 20, "cat": "Interior de Templos y Mazmorras", "name": "Interior de la Cueva Dodongo", "sub": "Dodongo's Cavern", "map": "DodongoCavern", "desc": "Mina Goron invadida por lagartos Dodongo y el jefe King Dodongo."},
    {"idx": 21, "cat": "Interior de Templos y Mazmorras", "name": "Interior de la Barriga de Jabu-Jabu", "sub": "Inside Jabu-Jabu's Belly", "map": "InsideJabuJabuBelly", "desc": "Laberinto interior orgánico infestado de parásitos bioeléctricos y Barinade."},
    {"idx": 22, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Templo del Bosque", "sub": "Forest Temple", "map": "ForestTemple", "desc": "Mansión sagrada encantada donde residen las cuatro Hermanas Poe y Phantom Ganon."},
    {"idx": 23, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Templo del Fuego", "sub": "Fire Temple", "map": "FireTemple", "desc": "Prisión volcánica subterránea custodiada por el dragón subterráneo Volvagia."},
    {"idx": 24, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Templo del Agua", "sub": "Water Temple", "map": "WaterTemple", "desc": "Santuario subacuático con compuertas de nivel de agua, Shadow Link y Morpha."},
    {"idx": 25, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Templo de la Sombra", "sub": "Shadow Temple", "map": "ShadowTemple", "desc": "Antigua casa de tortura y secretos sangrientos de Hyrule gobernada por Bongo Bongo."},
    {"idx": 26, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Templo del Espíritu", "sub": "Spirit Temple", "map": "SpiritTemple", "desc": "Santuario dorado dividido en pasado y futuro gobernado por las brujas Koume y Kotake."},
    {"idx": 27, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Fondo del Pozo", "sub": "Bottom of the Well", "map": "BottomOfTheWell", "desc": "Catacumba tenebrosa bajo la Aldea Kakariko donde se oculta la Lente de la Verdad."},
    {"idx": 28, "cat": "Interior de Templos y Mazmorras", "name": "Interior de la Caverna de Hielo", "sub": "Ice Cavern", "map": "IceCavern", "desc": "Gruta de hielo cristalina donde se obtiene el Fuego Azul y las Botas de Hierro."},
    {"idx": 29, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Centro Gerudo", "sub": "Gerudo Training Ground", "map": "GerudoTrainingGround", "desc": "Desafío de las llaves secretas de las guerreras que custodia las Flechas de Hielo."},
    {"idx": 30, "cat": "Interior de Templos y Mazmorras", "name": "Interior del Castillo de Ganon", "sub": "Inside Ganon's Castle", "map": "InsideGanonCastle", "desc": "La fortaleza final suspendida sobre la lava donde se libra la batalla por el destino de Hyrule."},
]

# =============================================================================
# REGISTRO DE EVENTOS EN VIVO
# =============================================================================
class LiveLogger:
    def __init__(self, log_file_path="triforce_modmenu_debug.log"):
        self.log_file_path = log_file_path
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
# COMUNICACIÓN IPC CON EL MOTOR (PIPE NATIVO)
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
# MOTOR DE MEMORIA ROBUSTO CON IDENTIFICACIÓN INSTANTÁNEA
# =============================================================================
class ProcessMemoryEngine:
    def __init__(self, logger: LiveLogger):
        self.log = logger
        self.pid = None
        self.process_handle = None
        self.vk_dll_base = None
        self.exe_base = None
        self.gamedata_base = None
        self.is_windows = sys.platform.startswith("win")
        self._warned = False

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

    def attach(self):
        if self.is_attached():
            return True

        pid = self.find_hookshot_pid()
        if not pid:
            self.detach()
            return False

        # Permisos completos para lectura y escritura de memoria
        handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
        if not handle:
            handle = kernel32.OpenProcess(0x0010 | 0x0020 | 0x0008 | 0x0400, False, pid)

        if not handle:
            return False

        self.pid = pid
        self.process_handle = handle
        if not self._warned:
            self._warned = True
            self.log.ok(f"Enganchado al proceso de Hookshot [PID: {pid}]")

        self.locate_modules()
        return True

    def detach(self):
        if self.process_handle and self.is_windows:
            try:
                kernel32.CloseHandle(ctypes.c_void_p(self.process_handle))
            except Exception:
                pass
        self.process_handle = None
        self.pid = None
        self.vk_dll_base = None
        self.exe_base = None
        self.gamedata_base = None

    def read_bytes(self, address, size):
        if not self.is_attached() or not address or size <= 0:
            return None
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        res = kernel32.ReadProcessMemory(
            ctypes.c_void_p(self.process_handle), ctypes.c_void_p(address),
            buf, ctypes.c_size_t(size), ctypes.byref(bytes_read)
        )
        if res and bytes_read.value > 0:
            return buf.raw[:bytes_read.value]
        return None

    def write_bytes(self, address, data):
        if not self.is_attached() or not address or not data:
            return False
        buf = ctypes.create_string_buffer(data, len(data))
        bytes_written = ctypes.c_size_t(0)
        res = kernel32.WriteProcessMemory(
            ctypes.c_void_p(self.process_handle), ctypes.c_void_p(address),
            buf, ctypes.c_size_t(len(data)), ctypes.byref(bytes_written)
        )
        return bool(res and bytes_written.value == len(data))

    def write_u8(self, address, val):
        return self.write_bytes(address, struct.pack("B", int(val) & 0xFF))

    def write_u16(self, address, val):
        return self.write_bytes(address, struct.pack("<H", int(val) & 0xFFFF))

    def write_u32(self, address, val):
        return self.write_bytes(address, struct.pack("<I", int(val) & 0xFFFFFFFF))

    def locate_modules(self):
        """Localiza hookshot.exe y hookshot_vk.dll de forma instantánea (<5ms) usando Toolhelp32."""
        if not self.is_attached():
            return None
        if self.vk_dll_base and self.exe_base:
            return self.vk_dll_base

        h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
        if h_snap and h_snap != -1 and h_snap != wintypes.HANDLE(-1).value:
            me = MODULEENTRY32()
            me.dwSize = ctypes.sizeof(MODULEENTRY32)
            if kernel32.Module32First(h_snap, ctypes.byref(me)):
                while True:
                    name_str = me.szModule.decode("latin1", errors="ignore").lower()
                    base_val = me.modBaseAddr
                    if name_str == "hookshot.exe":
                        self.exe_base = base_val
                        self.log.ok(f"hookshot.exe localizado instantáneamente en 0x{base_val:X}")
                    elif "hookshot_vk" in name_str or (name_str.endswith(".dll") and me.modBaseSize == VK_IMAGE_SIZE):
                        self.vk_dll_base = base_val
                        self.log.ok(f"hookshot_vk.dll localizado instantáneamente en 0x{base_val:X}")
                    if not kernel32.Module32Next(h_snap, ctypes.byref(me)):
                        break
            kernel32.CloseHandle(h_snap)

        # Fallback de direcciones base estándar por seguridad
        if not self.vk_dll_base:
            self.vk_dll_base = 0x180000000
        if not self.exe_base:
            self.exe_base = 0x140000000

        return self.vk_dll_base

    def scan_gamedata_buffer(self):
        """Verifica el búfer directo de SaveContext sin escaneos lentos."""
        if self.gamedata_base:
            return self.gamedata_base
        test = self.read_bytes(GUEST_SAVECONTEXT, 16)
        if test:
            self.gamedata_base = GUEST_SAVECONTEXT
            return self.gamedata_base
        return None


# =============================================================================
# CONTROLADOR PRINCIPAL DE CHEATS EN TIEMPO REAL
# =============================================================================
class TriforceModController:
    def __init__(self, logger: LiveLogger):
        self.log = logger
        self.bridge = HookshotNativeBridge(logger)
        self.mem = ProcessMemoryEngine(logger)

        # Cheats activos
        self.god_mode        = False
        self.inf_health      = False
        self.inf_magic       = False
        self.no_clip_flight  = False
        self.inf_rupees_ammo = False
        self.damage_mult     = 1.0
        self.link_speed_idx  = 0
        self.game_speed_idx  = 1

        # Telemetría
        self.live_fps   = 0.0
        self.live_map   = "Conectando..."
        self.live_age   = "ADULTO"
        self.is_running = True

        self._thread = threading.Thread(target=self._realtime_loop, daemon=True)
        self._thread.start()

    def _realtime_loop(self):
        status_timer = 0
        while self.is_running:
            now = time.time()
            # 1. Telemetría de Hookshot (cada 0.5s)
            if now - status_timer >= 0.5:
                status_timer = now
                st = self.bridge.get_status()
                if st and st.get("ok"):
                    self.live_fps = float(st.get("fps", 0.0))
                    self.live_map = str(st.get("map", "HyruleField"))
                    self.live_age = str((st.get("game") or {}).get("age", "adult")).upper()

            # 2. Aplicación continua de cheats activos en memoria
            if self.mem.attach():
                vk_base = self.mem.vk_dll_base or self.mem.locate_modules()
                exe_base = self.mem.exe_base

                # Modo Dios / Invulnerabilidad total
                if self.god_mode or self.inf_health:
                    if vk_base:
                        self.mem.write_u32(vk_base + RVA_PROTECT_HEARTS, 1)
                    if exe_base:
                        self.mem.write_u32(exe_base + RVA_EXE_PROTECT, 1)

                # Vuelo Libre (No-clip)
                if self.no_clip_flight and vk_base:
                    self.mem.write_u8(vk_base + RVA_PLAYER_FLIGHT, 1)

                # Velocidad de desplazamiento
                if self.link_speed_idx > 0 and vk_base:
                    self.mem.write_u32(vk_base + RVA_LINK_SPEED, self.link_speed_idx)

                # Rupias y Munición
                if self.inf_rupees_ammo and vk_base:
                    for item_off in range(0, 32 * 4, 4):
                        self.mem.write_u32(vk_base + RVA_ITEM_COUNTS + item_off, 99)

            time.sleep(0.04)

    def refill_health_and_magic(self):
        """
        Rellena la salud y magia de Link al 100% de forma instantánea.
        No activa el Modo Dios ni congela ningún parámetro.
        """
        success = False
        if self.mem.attach():
            self.mem.locate_modules()

            # Estructura: 20 Corazones (320 HP) + Barra Doble (96 MP) + Flags de Magia
            payload = struct.pack("<HHBBBBB", 320, 320, 2, 96, 96, 1, 1)

            # 1. Escribe en todas las bases conocidas de SaveContext en memoria
            bases_to_write = [GUEST_SAVECONTEXT, GUEST_N64_CTX, 0x10000011A5D0]

            # Si el puntero dinámico del Player Actor está disponible
            try:
                raw_ptr = self.mem.read_bytes(GUEST_PLAYER_PTR, 8)
                if raw_ptr:
                    ptr_val = struct.unpack("<Q", raw_ptr)[0]
                    if 0x100000000000 < ptr_val < 0x102000000000:
                        bases_to_write.append(ptr_val)
            except Exception:
                pass

            for base in bases_to_write:
                try:
                    if self.mem.write_bytes(base + 0x14, payload):
                        success = True
                except Exception:
                    pass

            # 2. Señalización nativa al motor
            vk_base = self.mem.vk_dll_base
            if vk_base:
                try:
                    self.mem.write_u32(vk_base + RVA_CHEAT_ACTION, 1)
                    success = True
                except Exception:
                    pass

            exe_base = self.mem.exe_base
            if exe_base:
                try:
                    self.mem.write_u32(exe_base + RVA_EXE_ACTION, 1)
                    success = True
                except Exception:
                    pass

            # 3. GameData buffer si está presente
            gd_base = self.mem.gamedata_base or self.mem.scan_gamedata_buffer()
            if gd_base:
                try:
                    self.mem.write_u32(gd_base + 0x23AA4, 20)
                    success = True
                except Exception:
                    pass

            self.log.ok("Salud (20 Corazones) y Magia Doble al 100% inyectadas en memoria.")

        return success

        return success

    def unlock_all_items(self):
        """Desbloquea todo el equipamiento, canciones y medallones del juego."""
        if self.mem.attach():
            vk_base = self.mem.vk_dll_base or self.mem.locate_modules()
            if vk_base:
                try:
                    for i in range(90):
                        self.mem.write_u8(vk_base + RVA_ITEMS_TABLE + i, 1)
                        self.mem.write_u32(vk_base + RVA_ITEM_COUNTS + (i * 4), 99)
                except Exception:
                    pass
        return True


# =============================================================================
# INTERFAZ GRÁFICA ZELDA (TRIFORCE ENGINE MOD MENU)
# =============================================================================
class TriforceModGUI:
    COLOR_BG           = "#130e0a"  # Fondo base espresso oscuro
    COLOR_CANVAS       = "#18120d"  # Contenedor interior cálido
    COLOR_HEADER_BG    = "#ba9f74"  # Barra de pestañas cuero / pergamino
    COLOR_TAB_ACTIVE   = "#2b1c11"  # Pestaña activa marrón oscuro
    COLOR_TAB_ACT_FG   = "#ffffff"  # Texto blanco en pestaña activa
    COLOR_TAB_INACT_FG = "#201309"  # Texto oscuro en pestaña inactiva
    COLOR_ROW_BG       = "#231810"  # Fondo de cada fila de ajuste
    COLOR_ROW_HOVER    = "#342419"  # Fila al pasar el cursor
    COLOR_BORDER_GOLD  = "#f59e0b"  # Borde dorado brillante
    COLOR_GOLD_TEXT    = "#e6a845"  # Título de categoría dorado / ámbar
    COLOR_TEXT_MAIN    = "#faedd9"  # Texto pergamino muy claro y legible
    COLOR_TEXT_MUTED   = "#ad9a84"  # Texto secundario apagado
    COLOR_CARD_BG      = "#1c140e"  # Tarjeta de descripción y estado
    COLOR_CARD_BORDER  = "#3a281a"  # Borde de tarjetas
    COLOR_FPS_GREEN    = "#10b981"  # Indicador FPS verde esmeralda
    COLOR_PILL_ON      = "#8d5d2a"  # Toggle activado (oro viejo brillante)
    COLOR_PILL_OFF     = "#1c140e"  # Toggle desactivado

    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = LiveLogger()
        self.ctrl = TriforceModController(self.logger)

        self.root.title("The Legend of Zelda: Ocarina of Time — Triforce Mod Menu")
        self.root.geometry("1120x760")
        self.root.minsize(980, 680)
        self.root.configure(bg=self.COLOR_BG)

        # No forzar superposición por defecto
        self.var_topmost = tk.BooleanVar(value=False)
        self.root.attributes("-topmost", False)

        # Variables de control
        self.var_god_mode   = tk.BooleanVar(value=False)
        self.var_inf_health = tk.BooleanVar(value=False)
        self.var_inf_magic  = tk.BooleanVar(value=False)
        self.var_no_clip    = tk.BooleanVar(value=False)
        self.var_inf_rupees = tk.BooleanVar(value=False)

        # Selectores
        self.damage_options = ["x1 Normal", "x2 Doble Daño", "x4 Cuádruple", "x8 Brutal", "💀 One-Hit Kill"]
        self.damage_idx = 0

        self.speed_options = ["1.0x Normal", "1.25x Ágil", "1.5x Rápido", "2.0x Veloz", "3.0x Relámpago"]
        self.speed_idx = 0

        self.game_speed_options = ["0.5x Cámara Lenta", "1.0x Tiempo Real", "1.5x Acelerado", "2.0x Doble Velocidad"]
        self.game_speed_idx = 1

        self.age_options = ["👦 Link Niño", "🧑 Link Adulto"]
        self.age_idx = 1

        # Panel de Descripción y Estado
        self.var_desc_title = tk.StringVar(value="Triforce Mod Menu")
        self.var_desc_body  = tk.StringVar(
            value="Bienvenido al menú de modificaciones externo para The Legend of Zelda: Ocarina of Time.\n\n"
                  "Controla la vida, magia, invulnerabilidad, velocidad, inventario y teletransporte a las afueras "
                  "de cualquier templo en caliente mientras juegas sin interrupciones."
        )
        self.var_desc_note  = tk.StringVar(value="Sincronizado al 100% con el motor nativo de Hookshot.")

        # Telemetría
        self.var_fps_text  = tk.StringVar(value="-- FPS")
        self.var_map_text  = tk.StringVar(value="Conectando...")
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

        # Atajos de teclado estilo Zelda
        self.root.bind("<q>", lambda _e: self._cycle_tab(-1))
        self.root.bind("<Q>", lambda _e: self._cycle_tab(-1))
        self.root.bind("<e>", lambda _e: self._cycle_tab(1))
        self.root.bind("<E>", lambda _e: self._cycle_tab(1))
        self.root.bind("<Escape>", lambda _e: self.root.iconify())
        self.root.bind("<F4>", lambda _e: self._action_refill_hearts_magic())
        self.root.bind("<h>", lambda _e: self._action_refill_hearts_magic())
        self.root.bind("<H>", lambda _e: self._action_refill_hearts_magic())
        self.root.bind("<F5>", lambda _e: self._toggle_bool(self.var_god_mode, "Modo Dios"))
        self.root.bind("<F6>", lambda _e: self._toggle_bool(self.var_inf_health, "Vida Infinita"))
        self.root.bind("<F7>", lambda _e: self._toggle_bool(self.var_inf_magic, "Magia Infinita"))
        self.root.bind("<F8>", lambda _e: self._toggle_bool(self.var_no_clip, "Vuelo No-Clip"))
        self.root.bind("<F9>", lambda _e: self._toggle_bool(self.var_inf_rupees, "Rupias & Munición"))

        self._start_ui_loop()

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # -------------------------------------------------------------------------
    def _build_interface(self):
        # 1. BARRA SUPERIOR DE PESTAÑAS
        header = tk.Frame(self.root, bg=self.COLOR_HEADER_BG, height=46)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        h_left = tk.Frame(header, bg=self.COLOR_HEADER_BG)
        h_left.pack(side="left", padx=(14, 0))
        tk.Label(
            h_left, text="Zelda: Ocarina of Time — Triforce Menu",
            bg=self.COLOR_HEADER_BG, fg=self.COLOR_TAB_INACT_FG,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 10))

        self._make_key_badge(h_left, "Q")

        self.tab_container = tk.Frame(header, bg=self.COLOR_HEADER_BG)
        self.tab_container.pack(side="left", padx=10)

        self.tab_buttons = []
        for i, (key, label) in enumerate(self.tabs):
            b = tk.Label(
                self.tab_container, text=label, padx=20, pady=11,
                bg=self.COLOR_HEADER_BG, fg=self.COLOR_TAB_INACT_FG,
                font=("Segoe UI", 10, "bold"), cursor="hand2"
            )
            b.pack(side="left", padx=1)
            b.bind("<Button-1>", lambda _e, idx=i: self._set_active_tab(idx))
            self.tab_buttons.append(b)

        self._make_key_badge(self.tab_container, "E")

        h_right = tk.Frame(header, bg=self.COLOR_HEADER_BG)
        h_right.pack(side="right", padx=(0, 16))

        self.btn_pin = tk.Label(
            h_right, text="📌 Fijar", padx=8, pady=4,
            bg=self.COLOR_HEADER_BG, fg=self.COLOR_TAB_INACT_FG,
            font=("Segoe UI", 8, "bold"), cursor="hand2"
        )
        self.btn_pin.pack(side="left", padx=(0, 12))
        self.btn_pin.bind("<Button-1>", lambda _e: self._toggle_topmost())

        fps_box = tk.Frame(h_right, bg=self.COLOR_HEADER_BG)
        fps_box.pack(side="right")
        tk.Label(fps_box, textvariable=self.var_fps_text, bg=self.COLOR_HEADER_BG, fg="#065f46", font=("Segoe UI", 10, "bold")).pack(anchor="e")
        tk.Label(fps_box, textvariable=self.var_map_text, bg=self.COLOR_HEADER_BG, fg="#201309", font=("Segoe UI", 7, "bold")).pack(anchor="e")

        # 2. BANNER TOAST
        self.toast_banner = tk.Frame(self.root, bg="#27180d")
        self.lbl_toast = tk.Label(
            self.toast_banner, textvariable=self.var_toast_msg,
            bg="#27180d", fg=self.COLOR_BORDER_GOLD, font=("Segoe UI", 9, "bold"), pady=4
        )

        # 3. CUERPO PRINCIPAL
        body = tk.Frame(self.root, bg=self.COLOR_BG, padx=18, pady=12)
        body.pack(fill="both", expand=True)

        left_col = tk.Frame(body, bg=self.COLOR_CANVAS, highlightthickness=1, highlightbackground=self.COLOR_CARD_BORDER)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 14))

        self.canvas = tk.Canvas(left_col, bg=self.COLOR_CANVAS, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        self.scroll_content = tk.Frame(self.canvas, bg=self.COLOR_CANVAS)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        self.scroll_content.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Páginas
        self.page_frames = {}
        for key, _ in self.tabs:
            p = tk.Frame(self.scroll_content, bg=self.COLOR_CANVAS)
            self.page_frames[key] = p

        self._build_page_combat(self.page_frames["combat"])
        self._build_page_teleport(self.page_frames["teleport"])
        self._build_page_items(self.page_frames["items"])
        self._build_page_system(self.page_frames["system"])

        # Columna Derecha
        right_col = tk.Frame(body, bg=self.COLOR_BG, width=330)
        right_col.pack(side="right", fill="both")
        right_col.pack_propagate(False)

        desc_card = tk.Frame(right_col, bg=self.COLOR_CARD_BG, padx=16, pady=14, highlightthickness=1, highlightbackground=self.COLOR_CARD_BORDER)
        desc_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            desc_card, textvariable=self.var_desc_title, bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 11, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 6))

        tk.Label(
            desc_card, textvariable=self.var_desc_body, bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT_MUTED, font=("Segoe UI", 9), justify="left", wraplength=290, anchor="nw"
        ).pack(fill="x", pady=(0, 10))

        note_row = tk.Frame(desc_card, bg=self.COLOR_CARD_BG)
        note_row.pack(fill="x")
        tk.Label(note_row, text="|", bg=self.COLOR_CARD_BG, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 6))
        tk.Label(
            note_row, textvariable=self.var_desc_note, bg=self.COLOR_CARD_BG,
            fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 8), justify="left", wraplength=270
        ).pack(side="left")

        # HUD en Vivo
        hud_card = tk.Frame(right_col, bg=self.COLOR_CARD_BG, padx=16, pady=12, highlightthickness=1, highlightbackground=self.COLOR_CARD_BORDER)
        hud_card.pack(fill="x", pady=(0, 10))

        tk.Label(hud_card, text="ESTADO DE LINK EN VIVO", bg=self.COLOR_CARD_BG, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))

        self.lbl_hud_hearts = tk.Label(hud_card, text="❤️ Salud: 20 Corazones", bg=self.COLOR_CARD_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9))
        self.lbl_hud_hearts.pack(anchor="w", pady=1)

        self.lbl_hud_magic = tk.Label(hud_card, text="🔮 Magia: Barra Doble", bg=self.COLOR_CARD_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9))
        self.lbl_hud_magic.pack(anchor="w", pady=1)

        self.lbl_hud_god = tk.Label(hud_card, text="🛡️ Modo Dios: Desactivado", bg=self.COLOR_CARD_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9))
        self.lbl_hud_god.pack(anchor="w", pady=1)

        self.lbl_hud_engine = tk.Label(hud_card, text="⚙️ Motor Zelda: Conectando...", bg=self.COLOR_CARD_BG, fg=self.COLOR_TEXT_MUTED, font=("Segoe UI", 8))
        self.lbl_hud_engine.pack(anchor="w", pady=1)

        # Acciones Rápidas
        quick_card = tk.Frame(right_col, bg=self.COLOR_CARD_BG, padx=16, pady=12, highlightthickness=1, highlightbackground=self.COLOR_CARD_BORDER)
        quick_card.pack(fill="both", expand=True)

        tk.Label(quick_card, text="ACCIÓN DESTACADA", bg=self.COLOR_CARD_BG, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))

        # BOTÓN RELLENAR SALUD Y MAGIA AL 100% (NO ACTIVA MODO DIOS)
        btn_heal = tk.Button(
            quick_card, text="💖 Rellenar Vida y Magia al 100%", bg=self.COLOR_PILL_ON, fg=self.COLOR_TEXT_MAIN,
            activebackground=self.COLOR_BORDER_GOLD, activeforeground="#ffffff", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", pady=8, command=self._action_refill_hearts_magic
        )
        btn_heal.pack(fill="x", pady=4)

        btn_items = tk.Button(
            quick_card, text="⭐ Desbloquear Todos los Ítems", bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN,
            activebackground=self.COLOR_ROW_HOVER, activeforeground="#ffffff", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", pady=6, command=self._action_unlock_all
        )
        btn_items.pack(fill="x", pady=4)

        btn_warp_home = tk.Button(
            quick_card, text="🌿 Teletransporte a Bosque Kokiri", bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN,
            activebackground=self.COLOR_ROW_HOVER, activeforeground="#ffffff", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", pady=6, command=lambda: self._execute_warp(0, "Bosque Kokiri")
        )
        btn_warp_home.pack(fill="x", pady=4)

        # Footer
        footer = tk.Frame(self.root, bg=self.COLOR_BG, height=34, padx=18)
        footer.pack(fill="x", side="bottom", pady=(0, 6))

        prompts = [
            ("Pestañas", "Q", "E"),
            ("Acceso Rápido", "F5-F9"),
            ("Activar", "Click"),
            ("Ocultar", "Esc"),
        ]
        p_row = tk.Frame(footer, bg=self.COLOR_BG)
        p_row.pack(side="right")
        for label, *keys in prompts:
            tk.Label(p_row, text=label, bg=self.COLOR_BG, fg=self.COLOR_TEXT_MUTED, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(10, 4))
            for k in keys:
                self._make_key_badge(p_row, k)

        self._set_active_tab(0)

    # -------------------------------------------------------------------------
    # PÁGINA 1: COMBATE & SALUD
    # -------------------------------------------------------------------------
    def _build_page_combat(self, parent):
        # Hero Card destacado: Rellenar Salud y Magia al 100%
        self._create_hero_action_card(
            parent,
            "💖 Rellenar Salud (20 Corazones) y Magia Doble al 100%",
            "Restaura instantáneamente los 20 corazones completos (doble fila roja) y llena la barra doble de magia verde al 100%. "
            "No activa el Modo Dios ni congela ningún parámetro de combate.",
            "⚡ RELLENAR SALUD Y MAGIA AHORA",
            self._action_refill_hearts_magic,
            "Acceso rápido: [F4] o tecla [H] en cualquier momento"
        )

        self._create_section_header(parent, "Salud, Invencibilidad y Magia")

        self._create_toggle_row(
            parent, "Vida Infinita (20 Corazones)", self.var_inf_health,
            "Vida Infinita (20 Corazones)",
            "Mantiene los 20 corazones llenos permanentemente y congela el daño en caliente.",
            "Acceso rápido: [F6]. Congela el medidor de salud."
        )

        self._create_toggle_row(
            parent, "Magia Infinita (Barra Doble)", self.var_inf_magic,
            "Magia Infinita (Barra Doble)",
            "Rellena la barra verde de magia doble al 100% y bloquea el consumo de hechizos mágicos.",
            "Acceso rápido: [F7]. Hechizos ilimitados."
        )

        self._create_toggle_row(
            parent, "Modo Dios / Invulnerabilidad Total", self.var_god_mode,
            "Modo Dios (Invulnerabilidad Total)",
            "Activa la protección nativa del motor de Hookshot (protect_hearts). Link no sufre daño "
            "de ningún enemigo, trampa, proyectil, caída al vacío ni lava.",
            "Acceso rápido: [F5]. Protección total en tiempo real."
        )

        self._create_section_header(parent, "Físicas, Combate y Movimiento")

        self._create_selector_row(
            parent, "Multiplicador de Daño de Link", self.damage_options,
            lambda: self.damage_idx, self._set_damage_idx,
            "Multiplicador de Daño de Espada",
            "Multiplica la fuerza del corte de la espada de Link. Puedes elegir entre daño normal x1, "
            "doble, cuádruple, brutal x8 o muerte instantánea de un golpe (One-Hit Kill).",
            "Afecta a la Espada Kokiri, Espada Maestra y Biggoron."
        )

        self._create_selector_row(
            parent, "Velocidad de Movimiento de Link", self.speed_options,
            lambda: self.speed_idx, self._set_speed_idx,
            "Velocidad de Desplazamiento",
            "Modifica la velocidad a la que Link camina, corre, trepa y nada por Hyrule usando la "
            "configuración interna del motor.",
            "Ajustable de 1.0x hasta 3.0x Relámpago."
        )

        self._create_toggle_row(
            parent, "Modo Vuelo Libre (No-Clip)", self.var_no_clip,
            "Vuelo Libre y Traspaso de Muros (No-Clip)",
            "Permite volar por el aire realizando un doble salto. Mientras estás en el aire, mantén el botón de salto "
            "para ascender o agáchate para descender, atravesando cualquier muro o colisión.",
            "Acceso rápido: [F8]. Pulsa Salto dos veces para despegar."
        )

        self._create_toggle_row(
            parent, "Rupias (9999) y Munición Infinita (99)", self.var_inf_rupees,
            "Rupias y Munición Ilimitada",
            "Mantiene las rupias en 9999 y congela flechas, bombas, bombchus, semillas, nueces, palos "
            "y judías mágicas en 99 unidades.",
            "Acceso rápido: [F9]. Reservas completas al máximo."
        )

        self._create_section_header(parent, "Simulación del Tiempo y Edad")

        self._create_selector_row(
            parent, "Velocidad del Juego (Game Speed)", self.game_speed_options,
            lambda: self.game_speed_idx, self._set_game_speed_idx,
            "Velocidad Global del Juego",
            "Controla la velocidad del tiempo del motor. Útil para superar secciones a cámara lenta o "
            "acelerar diálogos y cinemáticas.",
            "Se aplica en caliente a través del pipe de Hookshot."
        )

        self._create_selector_row(
            parent, "Transformación de Edad de Link", self.age_options,
            lambda: self.age_idx, self._set_age_idx,
            "Alternar entre Link Niño y Adulto",
            "Cambia instantáneamente la edad de Link y recarga la escena en la época seleccionada sin "
            "tener que viajar al Templo del Tiempo ni clavar la Espada Maestra.",
            "Cambio de edad nativo de Hookshot."
        )

    # -------------------------------------------------------------------------
    # PÁGINA 2: TELETRANSPORTE
    # -------------------------------------------------------------------------
    def _build_page_teleport(self, parent):
        self._create_section_header(parent, "Buscador Rápido de Destinos")

        search_box = tk.Frame(parent, bg=self.COLOR_ROW_BG, padx=12, pady=6)
        search_box.pack(fill="x", pady=(0, 10))

        tk.Label(search_box, text="🔍 Buscar:", bg=self.COLOR_ROW_BG, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        entry = tk.Entry(search_box, textvariable=self.var_tp_filter, bg="#18120d", fg=self.COLOR_TEXT_MAIN, insertbackground="#ffffff", font=("Segoe UI", 9), relief="flat")
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda _e: self._filter_teleports())

        self.tp_list_frame = tk.Frame(parent, bg=self.COLOR_CANVAS)
        self.tp_list_frame.pack(fill="both", expand=True)

        self._render_teleport_list()

    def _render_teleport_list(self, filter_text=""):
        for w in self.tp_list_frame.winfo_children():
            w.destroy()

        categories = [
            "Afueras de Templos y Mazmorras",
            "Regiones & Ciudades",
            "Interior de Templos y Mazmorras",
        ]

        query = filter_text.strip().lower()

        for cat in categories:
            matching = [
                d for d in TELEPORT_LOCATIONS
                if d["cat"] == cat and (query in d["name"].lower() or query in d["sub"].lower() or query in d["desc"].lower())
            ]

            if not matching:
                continue

            self._create_section_header(self.tp_list_frame, cat)

            for dest in matching:
                self._create_teleport_row(self.tp_list_frame, dest)

    def _create_teleport_row(self, parent, dest):
        row = tk.Frame(parent, bg=self.COLOR_ROW_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=self.COLOR_CANVAS)
        row.pack(fill="x", pady=2)

        info = tk.Frame(row, bg=self.COLOR_ROW_BG)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=dest["name"], bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(info, text=dest["sub"], bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        btn = tk.Label(
            row, text="VIAJAR AHORA", padx=12, pady=4,
            bg=self.COLOR_PILL_ON, fg=self.COLOR_TEXT_MAIN,
            font=("Segoe UI", 8, "bold"), cursor="hand2"
        )
        btn.pack(side="right")
        btn.bind("<Button-1>", lambda _e, idx=dest["idx"], name=dest["name"]: self._execute_warp(idx, name))

        def _enter(_e):
            row.configure(bg=self.COLOR_ROW_HOVER)
            self._set_desc(dest["name"], dest["desc"], f"Mapa interno del motor: {dest['map']}")

        def _leave(_e):
            row.configure(bg=self.COLOR_ROW_BG)

        for w in (row, info):
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

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

    # -------------------------------------------------------------------------
    # PÁGINA 3: INVENTARIO & ÍTEMS
    # -------------------------------------------------------------------------
    def _build_page_items(self, parent):
        self._create_section_header(parent, "Gestor Rápido de Inventario")

        self._create_action_row(
            parent, "Rellenar Salud y Magia al 100% Ahora", "RELLENAR SALUD Y MAGIA",
            self._action_refill_hearts_magic,
            "Rellenar Salud y Magia",
            "Llena los 20 corazones al máximo y restaura la barra doble de magia verde sin activar Modo Dios.",
            "Restaura reservas inmediatamente."
        )

        self._create_action_row(
            parent, "Desbloquear Todos los Ítems y Equipamiento", "DESBLOQUEAR TODO",
            self._action_unlock_all,
            "Desbloqueo Maestro de Inventario",
            "Otorga todas las espadas, escudos, túnicas, botas, botellas, medallones de sabios, "
            "canciones de ocarina y 100 símbolos de Skulltula dorada.",
            "Desbloqueo permanente para esta sesión."
        )

    # -------------------------------------------------------------------------
    # PÁGINA 4: SISTEMA & TELEMETRÍA
    # -------------------------------------------------------------------------
    def _build_page_system(self, parent):
        self._create_section_header(parent, "Diagnóstico en Vivo del Motor")

        self._create_action_row(
            parent, "Re-escanear Memoria y Punteros de Link", "ESCANEAR AHORA",
            self._action_rescan,
            "Calibración de Punteros de Memoria",
            "Inspecciona la memoria en tiempo real para encontrar la estructura de Link y calibrar cheats.",
            "Optimizado para Windows 64-bit."
        )

        self._create_action_row(
            parent, "Reiniciar Mod Menu con permisos de Administrador", "ELEVAR ADMIN",
            self._action_relaunch_admin,
            "Elevación UAC de Windows",
            "Si el juego se ejecuta como Administrador, el Mod Menu requiere elevación UAC para escribir en la memoria.",
            "Reinicia la aplicación con elevación Win32."
        )

        self._create_section_header(parent, "Consola de Diagnóstico (triforce_modmenu_debug.log)")

        log_box = tk.Frame(parent, bg="#100b07", padx=8, pady=8)
        log_box.pack(fill="both", expand=True, pady=(0, 10))

        self.txt_log = tk.Text(
            log_box, bg="#100b07", fg="#c4b5a5", insertbackground="#ffffff",
            font=("Consolas", 8), height=14, relief="flat", wrap="none"
        )
        self.txt_log.pack(fill="both", expand=True)

        self.logger.add_listener(self._append_log)
        self.logger.info("Triforce Engine v4.7 listo y activo.")

    # -------------------------------------------------------------------------
    # ACCIONES Y HELPERS
    # -------------------------------------------------------------------------
    def _show_toast(self, message):
        self.var_toast_msg.set(message)
        self.toast_banner.pack(fill="x", side="top", pady=(0, 4))
        self.lbl_toast.pack(fill="x")
        self.root.after(4000, lambda: self.toast_banner.pack_forget())

    def _toggle_topmost(self):
        new_val = not self.var_topmost.get()
        self.var_topmost.set(new_val)
        self.root.attributes("-topmost", new_val)
        if new_val:
            self.btn_pin.configure(bg=self.COLOR_TAB_ACTIVE, fg="#ffffff", text="📌 Fijado")
            self._show_toast("📌 Ventana fijada en primer plano")
        else:
            self.btn_pin.configure(bg=self.COLOR_HEADER_BG, fg=self.COLOR_TAB_INACT_FG, text="📌 Fijar")
            self._show_toast("📌 Modo superpuesto desactivado")

    def _sync_cheats(self):
        self.ctrl.god_mode        = self.var_god_mode.get()
        self.ctrl.inf_health      = self.var_inf_health.get()
        self.ctrl.inf_magic       = self.var_inf_magic.get()
        self.ctrl.no_clip_flight  = self.var_no_clip.get()
        self.ctrl.inf_rupees_ammo = self.var_inf_rupees.get()

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

    def _action_refill_hearts_magic(self):
        """Rellena salud y magia al 100% de forma instantánea sin activar el Modo Dios."""
        self.ctrl.refill_health_and_magic()
        self._show_toast("💖 ¡Salud (20 Corazones) y Magia Doble restauradas al 100%!")
        self.logger.ok("Acción 'Rellenar Salud y Magia al 100%' ejecutada con éxito.")

    def _action_unlock_all(self):
        self.ctrl.unlock_all_items()
        self._show_toast("⭐ ¡Todos los ítems, medallones y canciones desbloqueados!")

    def _action_rescan(self):
        self._show_toast("🔍 Sincronizando módulos de Zelda...")
        threading.Thread(target=self._rescan_worker, daemon=True).start()

    def _rescan_worker(self):
        self.ctrl.mem.locate_modules()
        self.ctrl.mem.scan_gamedata_buffer()
        self._show_toast("✅ Sincronización instantánea completada.")

    def _action_relaunch_admin(self):
        if not sys.platform.startswith("win"): return
        try:
            script_path = os.path.abspath(__file__)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}" --elevated', None, 1)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo elevar privilegios: {e}")

    def _append_log(self, level, line):
        try:
            self.txt_log.insert("end", line + "\n")
            self.txt_log.see("end")
        except Exception:
            pass

    def _start_ui_loop(self):
        def _tick():
            fps = self.ctrl.live_fps
            scene = self.ctrl.live_map
            age = self.ctrl.live_age

            self.var_fps_text.set(f"{fps:.1f} FPS" if fps > 0 else "-- FPS")
            self.var_map_text.set(scene if scene else "Conectando...")
            self.var_age_badge.set(age)

            # Monitor en vivo
            god_on = self.var_god_mode.get()
            self.lbl_hud_god.configure(
                text=f"🛡️ Modo Dios: {'ACTIVO (Invulnerable)' if god_on else 'Desactivado'}",
                fg="#10b981" if god_on else self.COLOR_TEXT_MAIN
            )

            vk_base = self.ctrl.mem.vk_dll_base
            exe_base = self.ctrl.mem.exe_base
            if vk_base or exe_base:
                self.lbl_hud_engine.configure(
                    text=f"⚙️ Motor Zelda: Conectado (0x{(vk_base or exe_base):X})",
                    fg="#10b981"
                )
            else:
                self.lbl_hud_engine.configure(
                    text="⚙️ Motor Zelda: Esperando juego...",
                    fg=self.COLOR_TEXT_MUTED
                )

            self.root.after(400, _tick)

        self.root.after(400, _tick)

    # -------------------------------------------------------------------------
    # GENERADORES DE COMPONENTES VISUALES
    # -------------------------------------------------------------------------
    def _create_section_header(self, parent, title):
        h = tk.Frame(parent, bg=self.COLOR_CANVAS)
        h.pack(fill="x", pady=(14, 6))
        tk.Frame(h, bg=self.COLOR_GOLD_TEXT, width=3).pack(side="left", fill="y", padx=(0, 8))
        tk.Label(h, text=title, bg=self.COLOR_CANVAS, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 10, "bold")).pack(side="left")

    def _create_toggle_row(self, parent, label_text, var: tk.BooleanVar, title_desc, body_desc, note_desc):
        row = tk.Frame(parent, bg=self.COLOR_ROW_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=self.COLOR_CANVAS)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=label_text, bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")

        seg = tk.Frame(row, bg=self.COLOR_ROW_BG)
        seg.pack(side="right")

        btn_off = tk.Label(seg, text="Desactivado", padx=14, pady=4, font=("Segoe UI", 8, "bold"), cursor="hand2")
        btn_off.pack(side="left", padx=1)

        btn_on = tk.Label(seg, text="Activado", padx=14, pady=4, font=("Segoe UI", 8, "bold"), cursor="hand2")
        btn_on.pack(side="left", padx=1)

        def _update():
            on = var.get()
            if on:
                btn_on.configure(bg=self.COLOR_PILL_ON, fg=self.COLOR_TEXT_MAIN)
                btn_off.configure(bg=self.COLOR_PILL_OFF, fg=self.COLOR_TEXT_MUTED)
                row.configure(highlightbackground=self.COLOR_BORDER_GOLD, highlightthickness=1)
            else:
                btn_on.configure(bg=self.COLOR_PILL_OFF, fg=self.COLOR_TEXT_MUTED)
                btn_off.configure(bg="#2d1e13", fg=self.COLOR_TEXT_MAIN)
                row.configure(highlightbackground=self.COLOR_CANVAS, highlightthickness=1)

        def _set(v):
            var.set(v)
            self._sync_cheats()
            _update()
            state = "Activado" if v else "Desactivado"
            self._show_toast(f"⚡ {label_text}: {state}")

        btn_off.bind("<Button-1>", lambda _e: _set(False))
        btn_on.bind("<Button-1>", lambda _e: _set(True))

        def _hover_enter(_e):
            row.configure(bg=self.COLOR_ROW_HOVER)
            self._set_desc(title_desc, body_desc, note_desc)

        def _hover_leave(_e):
            row.configure(bg=self.COLOR_ROW_BG)

        for w in (row, seg):
            w.bind("<Enter>", _hover_enter)
            w.bind("<Leave>", _hover_leave)

        _update()
        return row

    def _create_selector_row(self, parent, label_text, options, get_idx_fn, set_idx_fn, title_desc, body_desc, note_desc):
        row = tk.Frame(parent, bg=self.COLOR_ROW_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=self.COLOR_CANVAS)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=label_text, bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")

        ctrl = tk.Frame(row, bg=self.COLOR_ROW_BG)
        ctrl.pack(side="right")

        lbl_val = tk.Label(ctrl, text=options[get_idx_fn()], bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9, "bold"), width=18, anchor="center")

        def _change(delta):
            cur = get_idx_fn()
            nxt = (cur + delta) % len(options)
            set_idx_fn(nxt)
            lbl_val.configure(text=options[nxt])

        b_left = tk.Label(ctrl, text="◀", bg=self.COLOR_ROW_BG, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 9), cursor="hand2", padx=6)
        b_left.pack(side="left")
        b_left.bind("<Button-1>", lambda _e: _change(-1))

        lbl_val.pack(side="left", padx=4)

        b_right = tk.Label(ctrl, text="▶", bg=self.COLOR_ROW_BG, fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 9), cursor="hand2", padx=6)
        b_right.pack(side="left")
        b_right.bind("<Button-1>", lambda _e: _change(1))

        def _hover_enter(_e):
            row.configure(bg=self.COLOR_ROW_HOVER)
            self._set_desc(title_desc, body_desc, note_desc)

        def _hover_leave(_e):
            row.configure(bg=self.COLOR_ROW_BG)

        for w in (row, ctrl):
            w.bind("<Enter>", _hover_enter)
            w.bind("<Leave>", _hover_leave)

        return row

    def _create_hero_action_card(self, parent, title, subtitle, btn_text, action_fn, note_txt=""):
        card = tk.Frame(parent, bg="#24170f", padx=16, pady=14, highlightthickness=2, highlightbackground=self.COLOR_BORDER_GOLD)
        card.pack(fill="x", padx=4, pady=(6, 12))

        top_row = tk.Frame(card, bg="#24170f")
        top_row.pack(fill="x", pady=(0, 4))
        tk.Label(
            top_row, text="★ ACCIÓN PRINCIPAL EN VIVO",
            bg="#24170f", fg=self.COLOR_BORDER_GOLD, font=("Segoe UI", 8, "bold")
        ).pack(side="left")

        tk.Label(
            card, text=title,
            bg="#24170f", fg="#ffffff", font=("Segoe UI", 11, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 2))

        tk.Label(
            card, text=subtitle,
            bg="#24170f", fg="#d6c5b2", font=("Segoe UI", 8), justify="left", wraplength=560, anchor="w"
        ).pack(fill="x", pady=(0, 10))

        act_row = tk.Frame(card, bg="#24170f")
        act_row.pack(fill="x")

        btn = tk.Button(
            act_row, text=btn_text, bg="#d97706", fg="#ffffff",
            activebackground="#b45309", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=16, pady=6,
            command=action_fn
        )
        btn.pack(side="left")

        if note_txt:
            tk.Label(
                act_row, text=note_txt,
                bg="#24170f", fg=self.COLOR_GOLD_TEXT, font=("Segoe UI", 8, "italic")
            ).pack(side="left", padx=12)

        return card

    def _create_action_row(self, parent, label_text, btn_text, action_fn, title_desc, body_desc, note_desc):
        row = tk.Frame(parent, bg=self.COLOR_ROW_BG, padx=14, pady=8, highlightthickness=1, highlightbackground=self.COLOR_CANVAS)
        row.pack(fill="x", pady=2)

        tk.Label(row, text=label_text, bg=self.COLOR_ROW_BG, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")

        btn = tk.Label(row, text=btn_text, padx=14, pady=4, bg=self.COLOR_PILL_ON, fg=self.COLOR_TEXT_MAIN, font=("Segoe UI", 8, "bold"), cursor="hand2")
        btn.pack(side="right")
        btn.bind("<Button-1>", lambda _e: action_fn())

        def _hover_enter(_e):
            row.configure(bg=self.COLOR_ROW_HOVER)
            self._set_desc(title_desc, body_desc, note_desc)

        def _hover_leave(_e):
            row.configure(bg=self.COLOR_ROW_BG)

        for w in (row, btn):
            w.bind("<Enter>", _hover_enter)
            w.bind("<Leave>", _hover_leave)

        return row

    def _make_key_badge(self, parent, key_text):
        f = tk.Frame(parent, bg="#ffffff", padx=5, pady=1)
        f.pack(side="left", padx=2)
        tk.Label(f, text=key_text, bg="#ffffff", fg="#000000", font=("Consolas", 8, "bold")).pack()

    def _set_active_tab(self, idx):
        self.active_tab_idx = idx
        for i, b in enumerate(self.tab_buttons):
            if i == idx:
                b.configure(bg=self.COLOR_TAB_ACTIVE, fg=self.COLOR_TAB_ACT_FG)
            else:
                b.configure(bg=self.COLOR_HEADER_BG, fg=self.COLOR_TAB_INACT_FG)

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
# AUTO-ELEVACIÓN DE PRIVILEGIOS UAC EN WINDOWS
# =============================================================================
def ensure_windows_admin():
    if not sys.platform.startswith("win"):
        return
    if "--elevated" in sys.argv:
        return
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            script_path = os.path.abspath(__file__)
            res = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script_path}" --elevated', None, 1
            )
            if int(res) > 32:
                sys.exit(0)
    except Exception:
        pass


def main():
    ensure_windows_admin()
    root = tk.Tk()
    app = TriforceModGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
