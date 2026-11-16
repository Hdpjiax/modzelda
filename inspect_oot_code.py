with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

# Let's inspect sec4 VA in hookshot.exe
import pefile
pe = pefile.PE(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe")
sec4 = pe.sections[3] # Section 4
print("Sec4 Name:", sec4.Name.decode().strip(), "VA:", hex(sec4.VirtualAddress), "Raw:", hex(sec4.PointerToRawData))

# hos_oot_protect_hearts -> Val: 0x8A580D0, Sec: 4
# RVA = sec4.VirtualAddress + 0x8A580D0
rva_protect = sec4.VirtualAddress + 0x8A580D0
print(f"hos_oot_protect_hearts RVA: 0x{rva_protect:X}")

# hos_oot_live_action -> Val: 0x8A585C8, Sec: 4
rva_action = sec4.VirtualAddress + 0x8A585C8
print(f"hos_oot_live_action RVA: 0x{rva_action:X}")

# Disassemble hos_oot_hearts_enabled at Val 0x1965F5A0 (Sec 1)
sec1 = pe.sections[0]
foff_hearts = sec1.PointerToRawData + 0x1965F5A0
code_hearts = data[foff_hearts:foff_hearts+64]
print("hos_oot_hearts_enabled hex:", code_hearts[:32].hex())

# Disassemble hos_oot_lift_player at Val 0x1965FE40
foff_lift = sec1.PointerToRawData + 0x1965FE40
code_lift = data[foff_lift:foff_lift+128]
print("hos_oot_lift_player hex:", code_lift[:64].hex())
