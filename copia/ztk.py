#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  ZTK — TRIFORCE DESIGN SYSTEM (tkinter)
  Sistema de diseño "Switch 2 / Ocarina of Time" para el Mod Menu.
  Paleta obsidiana + oro Triforce, tipografía serif de display, iconos
  vectoriales dibujados y un motor de animación fluido (tweens a 60 Hz).
===============================================================================
"""

import math
import tkinter as tk

# =============================================================================
# PALETA — estilo MENÚ DEL JUEGO Ocarina of Time (Switch 2)
# Marrón cuero, dorado Triforce, pergamino, verde esmeralda
# =============================================================================
BG_DEEP     = "#2a1b0e"   # base muy oscura marrón
BG          = "#3d2b1f"   # fondo general cuero oscuro
PANEL       = "#4a3728"   # paneles cuero
CARD        = "#5d4230"   # tarjetas cuero medio
ROW         = "#6e533b"   # filas
ROW_HOVER   = "#8a6d4e"   # fila hover
ROW_ACTIVE  = "#a88663"   # fila seleccionada
BORDER      = "#d4a373"   # borde dorado suave
BORDER_SOFT = "#b88660"   # borde suave
BORDER_HARD = "#f0b429"   # borde dorado fuerte

GOLD        = "#f0b429"   # oro Triforce principal
GOLD_SOFT   = "#e6c86a"   # oro suave
GOLD_DIM    = "#8a6d2a"   # oro apagado
GOLD_GHOST  = "#5c4515"   # tinte oro tenue

TEXT        = "#fdf6e3"   # pergamino claro
TEXT_DIM    = "#d4c5a8"   # texto secundario
TEXT_FAINT  = "#b8a88c"   # hints

GREEN       = "#4ade80"   # válido / éxito
GREEN_DIM   = "#14381f"
RED         = "#ff5670"   # inválido / error
RED_DIM     = "#3d1a20"
BLUE        = "#5cc8ff"   # magia
BLUE_DIM    = "#12293d"
RUPEE       = "#3fd68c"   # rupias verde esmeralda
HEART       = "#ff4d4d"   # corazones rojo vivo
HEART_DIM   = "#3a1a1a"

# =============================================================================
# TIPOGRAFÍA
# =============================================================================
F_LOGO    = ("Georgia", 16, "bold")       # voz display: serif elegante (mundo Zelda)
F_TITLE   = ("Georgia", 13, "bold")       # títulos de página
F_SECTION = ("Georgia", 11, "bold")       # cabeceras de sección
F_UI      = ("Segoe UI", 10)              # etiquetas UI
F_UI_B    = ("Segoe UI", 10, "bold")      # etiquetas UI en negrita
F_SMALL   = ("Segoe UI", 9)               # texto pequeño
F_SMALL_B = ("Segoe UI", 9, "bold")
F_DATA    = ("Consolas", 11, "bold")      # lectura de datos (uso legítimo: medida)
F_DATA_S  = ("Consolas", 10)
F_TINY    = ("Segoe UI", 8, "bold")

# =============================================================================
# ANIMACIÓN — easing + lerp + ticker global de 60 Hz
# =============================================================================
def ease_out_cubic(t):
    t = 1.0 - t
    return 1.0 - t * t * t

def ease_out_expo(t):
    if t >= 1.0:
        return 1.0
    return 1.0 - math.pow(2.0, -10.0 * t)

def ease_out_back(t, s=1.70158):
    t -= 1.0
    return t * t * ((s + 1) * t + s) + 1.0

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    """Interpola dos colores '#rrggbb'."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(round(lerp(r1, r2, t)))
    g = int(round(lerp(g1, g2, t)))
    b = int(round(lerp(b1, b2, t)))
    return f"#{r:02x}{g:02x}{b:02x}"


class Ticker:
    """Un único bucle after() a ~60 Hz que impulsa todos los tweens activos."""
    _root = None
    _anims = []
    _running = False

    @classmethod
    def bind(cls, root):
        cls._root = root

    @classmethod
    def add(cls, tween):
        cls._anims.append(tween)
        if not cls._running:
            cls._running = True
            cls._root.after(8, cls._loop)

    @classmethod
    def _loop(cls):
        if cls._anims:
            now = cls._root.tk.call("clock", "milliseconds") if hasattr(cls._root, "tk") else 0
            still = []
            for a in cls._anims:
                a.step()
                if a.alive:
                    still.append(a)
            cls._anims = still
        if cls._anims:
            cls._root.after(16, cls._loop)
        else:
            cls._running = False


class Tween:
    """Interpolación con duración y easing; aplica vía apply(t, value)."""
    def __init__(self, frm, to, dur_ms, ease=ease_out_cubic, apply=None, done=None):
        self.frm = frm
        self.to = to
        self.dur = max(1, dur_ms)
        self.ease = ease
        self.apply = apply
        self.done = done
        self.t0 = None
        self.alive = True

    def start(self):
        Ticker.add(self)
        return self

    def step(self):
        if self.t0 is None:
            self.t0 = _now_ms()
        t = (_now_ms() - self.t0) / self.dur
        if t >= 1.0:
            t = 1.0
            self.alive = False
            if self.apply:
                self.apply(self.ease(1.0), self.to)
            if self.done:
                self.done()
            return
        if self.apply:
            self.apply(self.ease(t), lerp(self.frm, self.to, t))


def _now_ms():
    import time
    return time.monotonic() * 1000.0


def tween_value(frm, to, dur_ms, apply, ease=ease_out_cubic, done=None):
    return Tween(frm, to, dur_ms, ease, apply, done).start()


def tween_color(widget, prop, c1, c2, dur_ms, ease=ease_out_cubic, done=None):
    def _apply(t, _value):
        try:
            widget.configure(**{prop: lerp_color(c1, c2, t)})
        except Exception:
            pass
    return Tween(0.0, 1.0, dur_ms, ease, _apply, done).start()


# =============================================================================
# PRIMITIVAS DE DIBUJO
# =============================================================================
def rounded_rect(c, x1, y1, x2, y2, r, fill=None, outline=None, width=1):
    """Rectángulo redondeado (relleno + borde) sobre un canvas tkinter."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    if fill:
        c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
        c.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")
        for cx, cy, st in ((x1 + r, y1 + r, 90), (x2 - r, y1 + r, 0),
                           (x2 - r, y2 - r, 270), (x1 + r, y2 - r, 180)):
            c.create_arc(cx - r, cy - r, cx + r, cy + r, start=st, extent=90,
                         style="pieslice", fill=fill, outline="")
    if outline:
        for cx, cy, st in ((x1 + r, y1 + r, 90), (x2 - r, y1 + r, 0),
                           (x2 - r, y2 - r, 270), (x1 + r, y2 - r, 180)):
            c.create_arc(cx - r, cy - r, cx + r, cy + r, start=st, extent=90,
                         style="arc", outline=outline, width=width)
        c.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width)
        c.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width)
        c.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width)
        c.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width)


def heart_points(cx, cy, s):
    """Corazón paramétrico; s = radio aprox."""
    pts = []
    for i in range(48):
        t = math.pi * 2 * i / 48.0
        x = 16.0 * math.sin(t) ** 3
        y = 13.0 * math.cos(t) - 5.0 * math.cos(2 * t) - 2.0 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(cx + x * s / 17.0)
        pts.append(cy - y * s / 17.0)
    return pts


def draw_heart(c, cx, cy, s, color, filled=True, width=2):
    pts = heart_points(cx, cy, s)
    if filled:
        c.create_polygon(pts, fill=color, outline="", smooth=True)
    else:
        c.create_polygon(pts, fill="", outline=color, width=width, smooth=True)


def draw_triforce(c, cx, cy, s, color, width=2):
    """Las tres piezas doradas de la Trifuerza."""
    h = s * 0.90
    w = s
    # Triángulo central (invertido, arriba)
    c.create_polygon(cx, cy - h * 0.55, cx + w * 0.30, cy - h * 0.55 + w * 0.52,
                     cx - w * 0.30, cy - h * 0.55 + w * 0.52,
                     fill=color if width else color, outline="")
    # Inferiores
    c.create_polygon(cx - w * 0.34, cy + h * 0.42, cx - w * 0.04, cy + h * 0.42,
                     cx - w * 0.19, cy + h * 0.42 - w * 0.52, fill=color, outline="")
    c.create_polygon(cx + w * 0.34, cy + h * 0.42, cx + w * 0.04, cy + h * 0.42,
                     cx + w * 0.19, cy + h * 0.42 - w * 0.52, fill=color, outline="")


def _gem(c, cx, cy, s, color):
    """Gema / rupia."""
    c.create_polygon(cx, cy - s, cx + s * 0.72, cy - s * 0.18,
                     cx + s * 0.72, cy + s * 0.45, cx, cy + s,
                     cx - s * 0.72, cy + s * 0.45, cx - s * 0.72, cy - s * 0.18,
                     outline=color, width=2, fill="")
    c.create_line(cx, cy - s * 0.72, cx, cy + s * 0.45, fill=color, width=1)


def _flask(c, cx, cy, s, color):
    """Frasco de magia."""
    c.create_line(cx, cy - s, cx, cy - s * 0.30, fill=color, width=2)
    c.create_rectangle(cx - s * 0.22, cy - s, cx + s * 0.22, cy - s * 0.72,
                       outline=color, width=2)
    c.create_polygon(cx - s * 0.22, cy - s * 0.30, cx + s * 0.22, cy - s * 0.30,
                     cx + s * 0.85, cy + s * 0.85, cx - s * 0.85, cy + s * 0.85,
                     outline=color, width=2, fill="")
    c.create_line(cx - s * 0.45, cy + s * 0.25, cx + s * 0.45, cy + s * 0.25,
                  fill=color, width=2)


def _sword(c, cx, cy, s, color):
    c.create_line(cx - s * 0.7, cy + s * 0.75, cx + s * 0.55, cy - s * 0.55,
                  fill=color, width=3)
    c.create_line(cx + s * 0.30, cy - s * 0.30, cx + s * 0.75, cy - s * 0.75,
                  fill=color, width=3)
    c.create_line(cx - s * 0.45, cy + s * 0.45, cx + s * 0.05, cy + s * 0.95,
                  fill=color, width=3)


def _boot(c, cx, cy, s, color):
    c.create_line(cx - s * 0.55, cy - s * 0.85, cx - s * 0.55, cy + s * 0.25,
                  fill=color, width=2)
    c.create_line(cx - s * 0.55, cy + s * 0.25, cx + s * 0.75, cy + s * 0.25,
                  fill=color, width=2)
    c.create_line(cx + s * 0.75, cy + s * 0.25, cx + s * 0.75, cy + s * 0.75,
                  fill=color, width=2)
    c.create_line(cx - s * 0.55, cy + s * 0.75, cx + s * 0.75, cy + s * 0.75,
                  fill=color, width=2)


def _clock(c, cx, cy, s, color):
    c.create_oval(cx - s, cy - s, cx + s, cy + s, outline=color, width=2)
    c.create_line(cx, cy, cx, cy - s * 0.55, fill=color, width=2)
    c.create_line(cx, cy, cx + s * 0.42, cy + s * 0.18, fill=color, width=2)


def _figure(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.34, cy - s, cx + s * 0.34, cy - s * 0.32,
                  outline=color, width=2)
    c.create_arc(cx - s * 0.85, cy - s * 0.45, cx + s * 0.85, cy + s * 1.05,
                 start=180, extent=180, style="arc", outline=color, width=2)


def _pin(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.62, cy - s * 0.95, cx + s * 0.62, cy + s * 0.29,
                  outline=color, width=2)
    c.create_polygon(cx - s * 0.44, cy + s * 0.12, cx + s * 0.44, cy + s * 0.12,
                     cx, cy + s, outline=color, width=2, fill="")
    c.create_oval(cx - s * 0.22, cy - s * 0.55, cx + s * 0.22, cy - s * 0.11,
                  outline=color, width=2, fill="")


def _search(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.72, cy - s * 0.85, cx + s * 0.28, cy + s * 0.15,
                  outline=color, width=2)
    c.create_line(cx + s * 0.30, cy + s * 0.17, cx + s * 0.85, cy + s * 0.72,
                  fill=color, width=3)


def _shield(c, cx, cy, s, color):
    c.create_polygon(cx - s * 0.7, cy - s * 0.9, cx + s * 0.7, cy - s * 0.9,
                     cx + s * 0.7, cy + s * 0.15, cx, cy + s,
                     cx - s * 0.7, cy + s * 0.15, outline=color, width=2, fill="")


def _chest(c, cx, cy, s, color):
    c.create_rectangle(cx - s * 0.85, cy - s * 0.35, cx + s * 0.85, cy + s * 0.85,
                       outline=color, width=2)
    c.create_arc(cx - s * 0.85, cy - s * 1.0, cx + s * 0.85, cy + s * 0.30,
                 start=180, extent=180, style="arc", outline=color, width=2)
    c.create_line(cx, cy - s * 0.55, cx, cy + s * 0.85, fill=color, width=2)


def _check(c, cx, cy, s, color):
    c.create_line(cx - s * 0.75, cy, cx - s * 0.15, cy + s * 0.6,
                  fill=color, width=3)
    c.create_line(cx - s * 0.15, cy + s * 0.6, cx + s * 0.8, cy - s * 0.6,
                  fill=color, width=3)


def _cross(c, cx, cy, s, color):
    c.create_line(cx - s * 0.6, cy - s * 0.6, cx + s * 0.6, cy + s * 0.6,
                  fill=color, width=3)
    c.create_line(cx - s * 0.6, cy + s * 0.6, cx + s * 0.6, cy - s * 0.6,
                  fill=color, width=3)


def _bomb(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.72, cy - s * 0.25, cx + s * 0.72, cy + s * 0.9,
                  outline=color, width=2)
    c.create_line(cx + s * 0.25, cy - s * 0.25, cx + s * 0.55, cy - s * 0.7,
                  fill=color, width=2)
    c.create_oval(cx + s * 0.45, cy - s * 0.95, cx + s * 0.85, cy - s * 0.55,
                  outline=color, width=2, fill="")


def _seed(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.45, cy - s * 0.45, cx + s * 0.45, cy + s * 0.45,
                  outline=color, width=2)
    c.create_line(cx, cy - s * 0.45, cx + s * 0.55, cy - s * 0.9, fill=color, width=2)


def _nut(c, cx, cy, s, color):
    c.create_polygon(cx, cy - s * 0.85, cx + s * 0.75, cy - s * 0.42,
                     cx + s * 0.75, cy + s * 0.42, cx, cy + s * 0.85,
                     cx - s * 0.75, cy + s * 0.42, cx - s * 0.75, cy - s * 0.42,
                     outline=color, width=2, fill="")


def _stick(c, cx, cy, s, color):
    c.create_line(cx - s * 0.6, cy + s * 0.8, cx + s * 0.45, cy - s * 0.45,
                  fill=color, width=3)
    c.create_line(cx + s * 0.45, cy - s * 0.45, cx + s * 0.75, cy - s * 0.75,
                  fill=color, width=2)


def _bean(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.7, cy - s * 0.1, cx + s * 0.7, cy + s * 0.7,
                  outline=color, width=2)
    c.create_line(cx, cy - s * 0.1, cx, cy - s * 0.75, fill=color, width=2)
    c.create_oval(cx, cy - s * 0.95, cx + s * 0.45, cy - s * 0.45,
                  outline=color, width=2, fill="")


def _bow(c, cx, cy, s, color):
    c.create_arc(cx - s * 0.9, cy - s * 0.9, cx + s * 0.9, cy + s * 0.9,
                 start=300, extent=120, style="arc", outline=color, width=2)
    c.create_line(cx - s * 0.45, cy - s * 0.78, cx - s * 0.45, cy + s * 0.78,
                  fill=color, width=1)
    c.create_line(cx - s * 0.45, cy, cx + s * 0.6, cy, fill=color, width=2)


def _bolt(c, cx, cy, s, color):
    c.create_polygon(cx + s * 0.2, cy - s, cx - s * 0.55, cy + s * 0.15,
                     cx - s * 0.05, cy + s * 0.15, cx - s * 0.25, cy + s,
                     cx + s * 0.55, cy - s * 0.2, cx + s * 0.05, cy - s * 0.2,
                     fill=color, outline="")


def _gear(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.45, cy - s * 0.45, cx + s * 0.45, cy + s * 0.45,
                  outline=color, width=2)
    for i in range(8):
        a = math.pi * 2 * i / 8
        x1 = cx + math.cos(a) * s * 0.45
        y1 = cy + math.sin(a) * s * 0.45
        x2 = cx + math.cos(a) * s * 0.9
        y2 = cy + math.sin(a) * s * 0.9
        c.create_line(x1, y1, x2, y2, fill=color, width=3)


def _warn(c, cx, cy, s, color):
    c.create_polygon(cx, cy - s * 0.85, cx + s * 0.9, cy + s * 0.7,
                     cx - s * 0.9, cy + s * 0.7, outline=color, width=2, fill="")
    c.create_line(cx, cy - s * 0.35, cx, cy + s * 0.2, fill=color, width=3)
    c.create_line(cx, cy, cx, cy + s * 0.05, fill=color, width=3)


def _coin(c, cx, cy, s, color):
    c.create_oval(cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8,
                  outline=color, width=2)
    c.create_oval(cx - s * 0.45, cy - s * 0.45, cx + s * 0.45, cy + s * 0.45,
                  outline=color, width=2, fill="")


def _staff(c, cx, cy, s, color):
    c.create_line(cx, cy - s, cx, cy + s, fill=color, width=2)
    c.create_oval(cx - s * 0.4, cy - s * 1.05, cx + s * 0.4, cy - s * 0.25,
                  outline=color, width=2, fill="")


_ICONS = {
    "heart":     lambda c, cx, cy, s, col: draw_heart(c, cx, cy, s, col, filled=True),
    "heart_off": lambda c, cx, cy, s, col: draw_heart(c, cx, cy, s, col, filled=False),
    "rupee":     _gem,
    "coin":      _coin,
    "magic":     _flask,
    "sword":     _sword,
    "boot":      _boot,
    "clock":     _clock,
    "figure":    _figure,
    "pin":       _pin,
    "search":    _search,
    "shield":    _shield,
    "chest":     _chest,
    "check":     _check,
    "cross":     _cross,
    "bomb":      _bomb,
    "seed":      _seed,
    "nut":       _nut,
    "stick":     _stick,
    "bean":      _bean,
    "bow":       _bow,
    "bolt":      _bolt,
    "gear":      _gear,
    "warn":      _warn,
    "staff":     _staff,
}

ICON_NAMES = tuple(_ICONS.keys())


def draw_icon(c, name, cx, cy, s, color):
    fn = _ICONS.get(name)
    if fn:
        fn(c, cx, cy, s, color)


def icon_canvas(parent, name, size=18, color=TEXT_DIM, bg=None):
    """Mini-canvas con un icono vectorial dibujado."""
    cv = tk.Canvas(parent, width=size + 4, height=size + 4,
                   highlightthickness=0, bd=0, bg=bg or PANEL)
    draw_icon(cv, name, (size + 4) / 2.0, (size + 4) / 2.0, size / 2.0, color)
    return cv


# =============================================================================
# COMPONENTES
# =============================================================================
class FluidButton:
    """
    Botón fluido sobre canvas: hover con tween de color, glow dorado al pasar
    el cursor, hundimiento al pulsar y destello en el clic. Redibuja por frame.
    No hereda de tk.Frame para evitar conflictos de inicialización de widgets.
    """
    STYLE_PRIMARY = "primary"
    STYLE_SECONDARY = "secondary"
    STYLE_GHOST = "ghost"

    def __init__(self, parent, text, command=None, icon=None, style="primary",
                 width=200, height=40, bg=PANEL, font=None):
        self.command = command
        self.icon = icon
        self.text = text
        self.style = style
        self.font = font or ("Georgia", 11, "bold")
        self._w = width
        self._h = height
        self.enabled = True

        base = {
            "primary":   (GOLD,       "#000000", BORDER_HARD, GOLD_SOFT),  # texto negro sobre amarillo
            "secondary": (PANEL,      TEXT,      BORDER,      GOLD_SOFT),
            "ghost":     (BG_DEEP,    TEXT_DIM,  BORDER_SOFT, GOLD),
        }[style]

        self.c_idle_bg, self.c_idle_fg, self.c_idle_bd, self.c_hover_bd = base
        self.c_hover_bg = lerp_color(self.c_idle_bg, GOLD_SOFT, 0.15)
        self.c_press_bg = lerp_color(self.c_idle_bg, GOLD_DIM, 0.30)

        self.frame = tk.Frame(parent, bg=bg, highlightthickness=0, bd=0)
        self.canvas = tk.Canvas(self.frame, width=width, height=height,
                                highlightthickness=0, bd=0, bg=bg, cursor="hand2")
        self.canvas.pack()
        self._hover = 0.0
        self._press = 0.0
        self._flash = 0.0
        self._tw = self._measure()
        self._render()

        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        return self

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
        return self

    def place(self, **kwargs):
        self.frame.place(**kwargs)
        return self

    def _render(self):
        c = self.canvas
        c.delete("all")
        w, h = self._w, self._h
        pad = 2 * self._press
        x1, y1, x2, y2 = 1 + pad, 1 + pad, w - 1 - pad, h - 1 - pad

        bg = lerp_color(self.c_idle_bg, self.c_hover_bg, self._hover)
        bg = lerp_color(bg, self.c_press_bg, self._press)
        bd = lerp_color(self.c_idle_bd, self.c_hover_bd, self._hover)
        if self._flash > 0:
            bg = lerp_color(bg, "#ffffff", 0.35 * self._flash)
        if not self.enabled:
            bg = lerp_color(bg, PANEL, 0.55)
            bd = BORDER_SOFT

        rounded_rect(c, x1, y1, x2, y2, 8, fill=bg, outline=bd, width=2)

        fg = lerp_color(self.c_idle_fg, "#ffffff", self._hover)
        if not self.enabled:
            fg = TEXT_FAINT

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        if self.icon:
            tw = self._tw
            ix = cx - tw / 2.0 - 11
            draw_icon(c, self.icon, ix, cy, 9, fg)
        c.create_text(cx, cy, text=self.text, fill=fg, font=self.font, justify="center")

    def _measure(self):
        try:
            i = self.canvas.create_text(0, 0, text=self.text, font=self.font, anchor="nw")
            bb = self.canvas.bbox(i)
            self.canvas.delete(i)
            if bb:
                return bb[2] - bb[0]
        except Exception:
            pass
        return len(self.text) * 8

    def _on_enter(self, _e=None):
        tween_value(self._hover, 1.0, 150, self._apply_hover)

    def _apply_hover(self, _t, v):
        self._hover = v
        self._render()

    def _on_leave(self, _e=None):
        tween_value(self._hover, 0.0, 180, self._apply_hover)

    def _on_press(self, _e=None):
        if not self.enabled:
            return
        tween_value(0.0, 1.0, 90, self._apply_press)

    def _apply_press(self, _t, v):
        self._press = v
        self._render()

    def _on_release(self, _e=None):
        if not self.enabled:
            return
        tween_value(1.0, 0.0, 140, self._apply_press)
        tween_value(0.0, 1.0, 220, self._apply_flash)
        if self.command:
            self.command()

    def _apply_flash(self, _t, v):
        # 0 -> 1 pico -> 0
        self._flash = 1.0 - abs(2.0 * v - 1.0)
        self._render()

    def set_enabled(self, on):
        self.enabled = on
        self.canvas.configure(cursor="hand2" if on else "arrow")
        self._render()


class TogglePill(tk.Canvas):
    """Interruptor tipo Switch: píldora con pulgar deslizante y tween de color."""
    def __init__(self, parent, variable, command=None, width=56, height=28,
                 bg=PANEL, on_color=GOLD, off_color=ROW_ACTIVE):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bd=0, bg=bg, cursor="hand2")
        self.variable = variable
        self.command = command
        self.w = width
        self.h = height
        self.on_color = on_color
        self.off_color = off_color
        self._pos = 1.0 if variable.get() else 0.0
        self._render(self._pos)
        self.bind("<Button-1>", self._toggle)
        variable.trace_add("write", lambda *_: self._animate_to(1.0 if variable.get() else 0.0))

    def _toggle(self, _e=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _animate_to(self, target):
        tween_value(self._pos, target, 180, self._apply_pos, ease=ease_out_back)

    def _apply_pos(self, _t, v):
        self._pos = v
        self._render(v)

    def _render(self, p):
        self.delete("all")
        w, h = self.w, self.h
        r = h / 2.0
        track = lerp_color(self.off_color, self.on_color, p)
        rounded_rect(self, 1, 1, w - 1, h - 1, r, fill=track,
                     outline=lerp_color(BORDER, GOLD_SOFT, p), width=1)
        d = h - 8
        x = 4 + p * (w - 8 - d)
        thumb = lerp_color("#c9cede", "#ffffff", p)
        self.create_oval(x, 4, x + d, 4 + d, fill=thumb, outline="")
        self.create_oval(x + d * 0.28, 4 + d * 0.28, x + d * 0.72, 4 + d * 0.72,
                         fill=lerp_color("#9aa3b5", GOLD_SOFT, p), outline="")


class Stepper(tk.Frame):
    """Selector ◀ valor ▶ con pulso de realce al cambiar."""
    def __init__(self, parent, options, get_idx, set_idx, bg=PANEL, width=210):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)
        self.options = options
        self.get_idx = get_idx
        self.set_idx = set_idx
        self.bg = bg

        self.btn_l = self._arrow("◀", -1)
        self.val = tk.Label(self, text=options[get_idx()], bg=bg, fg=TEXT,
                            font=F_UI_B, width=17, anchor="center")
        self.val.pack(side="left", padx=6)
        self.btn_r = self._arrow("▶", 1)

    def _arrow(self, glyph, delta):
        b = tk.Label(self, text=glyph, bg=self.bg, fg=GOLD_SOFT,
                     font=F_UI_B, cursor="hand2", padx=7, pady=3)
        b.pack(side="left")
        b.bind("<Button-1>", lambda _e: self._change(delta))
        b.bind("<Enter>", lambda _e: b.configure(fg=GOLD))
        b.bind("<Leave>", lambda _e: b.configure(fg=GOLD_SOFT))
        return b

    def _change(self, delta):
        nxt = (self.get_idx() + delta) % len(self.options)
        self.set_idx(nxt)
        self.val.configure(text=self.options[nxt])
        tween_color(self.val, "bg", GOLD_GHOST, self.bg, 420)


class SectionLabel(tk.Frame):
    """Cabecera de sección: barra dorada + título serif espaciado (estilo menú del juego)."""
    def __init__(self, parent, title, bg=CARD, spaced=True):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)
        bar = tk.Frame(self, bg=GOLD, width=3)
        bar.pack(side="left", fill="y", padx=(0, 9))
        label = title
        if spaced:
            label = " ".join(list(title.upper()))
        tk.Label(self, text=label, bg=bg, fg=GOLD, font=("Georgia", 11, "bold")).pack(side="left")


class Badge(tk.Frame):
    """Etiqueta de estado (VÁLIDO / FUERA DE RANGO / ...)."""
    def __init__(self, parent, text, fg=GREEN, bg=GREEN_DIM, font=F_TINY):
        super().__init__(parent, bg=PANEL, highlightthickness=0, bd=0)
        self.label = tk.Label(self, text=text, bg=bg, fg=fg, font=font,
                              padx=8, pady=2)
        self.label.pack()

    def set(self, text, fg=GREEN, bg=GREEN_DIM):
        self.label.configure(text=text, fg=fg, bg=bg)


class ValueRow(tk.Frame):
    """
    Fila de dato para el escáner: icono + nombre + valor + estado.
    `reveal(delay_ms)` la hace aparecer con fade-in escalonado.
    """
    def __init__(self, parent, icon, label, value="—", status="", status_ok=True,
                 bg=ROW, border=BORDER_SOFT, ok_text="VÁLIDO", bad_text="REVISAR"):
        super().__init__(parent, bg=bg, padx=13, pady=7,
                         highlightthickness=1, highlightbackground=border)
        self.base_bg = bg
        self.ok_text = ok_text
        self.bad_text = bad_text
        ic = icon_canvas(self, icon, 17, GOLD_SOFT, bg)
        ic.pack(side="left", padx=(0, 10))
        tk.Label(self, text=label, bg=bg, fg=TEXT, font=F_UI).pack(side="left")
        self.value = tk.Label(self, text=value, bg=bg, fg=TEXT, font=F_DATA)
        self.value.pack(side="right", padx=(12, 0))
        self.badge = Badge(self, status or "—", GREEN if status_ok else RED,
                           GREEN_DIM if status_ok else RED_DIM)
        self.badge.pack(side="right")
        self._revealed = False

    def set_value(self, v, ok=True):
        self.value.configure(text=v)
        if ok is not None:
            self.badge.set(self.ok_text if ok else self.bad_text,
                           GREEN if ok else RED,
                           GREEN_DIM if ok else RED_DIM)

    def reveal(self, delay_ms=0):
        def _go():
            self.pack(fill="x", pady=2)
            tween_color(self, "bg", self.base_bg, self.base_bg, 1)  # no-op base
            # fade-in: de color de panel a color de fila
            for w in self.winfo_children():
                if isinstance(w, tk.Label):
                    tween_color(w, "bg", PANEL, self.base_bg, 260)
        if delay_ms > 0:
            self.after(delay_ms, _go)
        else:
            _go()


class HoverRow(tk.Frame):
    """
    Fila base con hover fluido y gancho de descripción contextual.
    `on_hover(title, body, note)` se dispara al entrar el cursor.
    """
    def __init__(self, parent, on_hover=None, bg=ROW, border=BORDER_SOFT):
        super().__init__(parent, bg=bg, padx=14, pady=8,
                         highlightthickness=1, highlightbackground=border)
        self.on_hover = on_hover
        self._bg = bg
        for w in (self,):
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _enter(self, _e=None):
        tween_color(self, "bg", self._bg, ROW_HOVER, 140)
        if self.on_hover:
            self.on_hover()

    def _leave(self, _e=None):
        tween_color(self, "bg", ROW_HOVER, self._bg, 200)


def bind_hover_recursive(widget, on_enter, on_leave):
    """Propaga hover de una fila a todos sus descendientes (labels, canvas...)."""
    for w in (widget,) + tuple(widget.winfo_children()):
        try:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
        except Exception:
            pass
        if isinstance(w, tk.Frame):
            bind_hover_recursive(w, on_enter, on_leave)


class ToastHost(tk.Frame):
    """Contenedor de toasts con deslizamiento de entrada y salida."""
    def __init__(self, parent, bg=BG_DEEP, max_toasts=3):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)
        self.queue = []
        self.active = []
        self.max = max_toasts
        self.place(relx=0.5, y=-60, anchor="n", width=520)
        self._busy = False

    def push(self, text, icon="check", fg=GOLD, border=GOLD_DIM):
        self.queue.append((text, icon, fg, border))
        self._pump()

    def _pump(self):
        if self._busy or not self.queue:
            return
        text, icon, fg, border = self.queue.pop(0)
        self._busy = True
        toast = tk.Frame(self, bg=CARD, padx=14, pady=9,
                         highlightthickness=1, highlightbackground=border)
        toast.pack(fill="x", pady=2)
        ic = icon_canvas(toast, icon, 15, fg, CARD)
        ic.pack(side="left", padx=(0, 9))
        tk.Label(toast, text=text, bg=CARD, fg=TEXT, font=F_SMALL_B,
                 wraplength=430, justify="left").pack(side="left")
        if len(self.active) >= self.max:
            old = self.active.pop(0)
            old.destroy()
        self.active.append(toast)

        start_y = -70.0
        end_y = 14.0

        def _apply(_t, y):
            self.place_configure(y=int(round(y)))

        def _exit():
            tween_value(end_y, start_y - 20, 240, _apply, ease=ease_in_out_sine,
                        done=self._dismiss)

        def _dismiss():
            toast.destroy()
            if toast in self.active:
                self.active.remove(toast)
            self._busy = False
            self._pump()

        tween_value(start_y, end_y, 300, _apply, ease=ease_out_expo)
        self.after(3200, _exit)


class ProgressBar(tk.Frame):
    """Barra de progreso redondeada con relleno animado."""
    def __init__(self, parent, bg=PANEL, height=8, width=420, fill=GOLD):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)
        self.canvas = tk.Canvas(self, width=width, height=height,
                                highlightthickness=0, bd=0, bg=bg)
        self.canvas.pack()
        self.w = width
        self.h = height
        self.fill = fill
        self._p = 0.0
        self._render()

    def _render(self):
        c = self.canvas
        c.delete("all")
        rounded_rect(c, 0, 0, self.w, self.h, self.h / 2.0, fill=ROW, outline=BORDER_SOFT, width=1)
        if self._p > 0.001:
            fw = max(self.h, self._p * self.w)
            rounded_rect(c, 0, 0, fw, self.h, self.h / 2.0, fill=self.fill, outline="")

    def set_progress(self, p, animate=True):
        p = max(0.0, min(1.0, p))
        if animate:
            tween_value(self._p, p, 280, self._apply, ease=ease_out_cubic)
        else:
            self._p = p
            self._render()

    def _apply(self, _t, v):
        self._p = v
        self._render()


class HeartsDisplay(tk.Canvas):
    """Fila de corazones dibujados (hasta 20) que refleja la salud en vivo."""
    def __init__(self, parent, max_hearts=20, size=13, bg=CARD):
        super().__init__(parent, width=size * 10 + 4, height=size + 6,
                         highlightthickness=0, bd=0, bg=bg)
        self.max_hearts = max_hearts
        self.size = size
        self.bg = bg
        self._shown = 0
        self._render(0, 20)

    def _render(self, cur_q, max_q):
        self.delete("all")
        s = self.size
        per_row = 10
        for i in range(self.max_hearts):
            row = i // per_row
            col = i % per_row
            cx = 10 + col * (s + 3)
            cy = 12 + row * (s + 2)
            filled = i < cur_q
            if filled:
                draw_heart(self, cx, cy, s / 2.0, HEART, filled=True)
            else:
                draw_heart(self, cx, cy, s / 2.0, HEART_DIM, filled=False, width=1)

    def update_hearts(self, cur_units, max_units):
        cur_q = max(0, min(self.max_hearts, int(round((cur_units or 0) / 4.0))))
        max_q = max(0, min(self.max_hearts, int(round((max_units or 0) / 4.0))))
        self._render(cur_q, max_q)


class TriforceMark(tk.Canvas):
    """Logo Trifuerza con latido dorado suave y órbita de partículas."""
    def __init__(self, parent, size=34, bg=BG_DEEP):
        super().__init__(parent, width=size + 8, height=size + 8,
                         highlightthickness=0, bd=0, bg=bg)
        self.size = size
        self.bg = bg
        self._pulse = 0.0
        self._render(0.0)

    def start_idle(self):
        def _cycle():
            tween_value(0.0, 1.0, 1400, self._apply, ease=ease_in_out_sine,
                        done=self._cycle)
        _cycle()

    def _cycle(self):
        tween_value(1.0, 0.0, 1400, self._apply, ease=ease_in_out_sine, done=self._cycle)

    def _apply(self, _t, v):
        self._pulse = v
        self._render(v)

    def _render(self, p):
        self.delete("all")
        w = self.size + 8
        cx, cy = w / 2.0, w / 2.0
        s = self.size / 2.0 + 1.5 * math.sin(p * math.pi)
        col = lerp_color(GOLD_SOFT, "#ffe08a", p)
        # halo suave
        for r, alpha_col in ((1.35, lerp_color(GOLD_DIM, GOLD_SOFT, p * 0.4)),):
            draw_triforce(self, cx, cy, s * r, alpha_col)
        draw_triforce(self, cx, cy, s, col)