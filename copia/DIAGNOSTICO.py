#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostico paso a paso del Mod Menu."""
import sys
import os

print("PASO 1: Python version OK:", sys.version)

try:
    import tkinter
    print("PASO 2: tkinter import OK")
except Exception as e:
    print("PASO 2 FALLO tkinter:", e)
    input("Presiona Enter para salir...")
    sys.exit(1)

try:
    from ztk import *
    print("PASO 3: ztk import OK")
except Exception as e:
    print("PASO 3 FALLO ztk:", e)
    import traceback; traceback.print_exc()
    input("Presiona Enter para salir...")
    sys.exit(1)

try:
    import modmenu
    print("PASO 4: modmenu import OK")
except Exception as e:
    print("PASO 4 FALLO modmenu:", e)
    import traceback; traceback.print_exc()
    input("Presiona Enter para salir...")
    sys.exit(1)

try:
    root = tkinter.Tk()
    print("PASO 5: Tk root creada OK")
    root.title("Test")
    root.geometry("300x200")
    lbl = tkinter.Label(root, text="Si ves esta ventana, tkinter funciona")
    lbl.pack(pady=50)
    root.after(2000, root.destroy)  # se cierra sola en 2 segundos
    root.mainloop()
    print("PASO 5: root.mainloop termino OK")
except Exception as e:
    print("PASO 5 FALLO tkinter GUI:", e)
    import traceback; traceback.print_exc()
    input("Presiona Enter para salir...")
    sys.exit(1)

print("TODO OK - el problema puede estar en ensure_windows_admin()")
input("Presiona Enter para salir...")
