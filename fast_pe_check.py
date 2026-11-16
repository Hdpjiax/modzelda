import struct

with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    f.seek(0x3C)
    pe_off = struct.unpack("<I", f.read(4))[0]
    f.seek(pe_off + 4 + 2)
    num_sections = struct.unpack("<H", f.read(2))[0]
    f.seek(pe_off + 4 + 16)
    opt_size = struct.unpack("<H", f.read(2))[0]
    sec_headers_off = pe_off + 24 + opt_size
    
    sections = []
    for i in range(num_sections):
        f.seek(sec_headers_off + i * 40)
        sec_name = f.read(8).rstrip(b"\x00").decode("latin1")
        vsize, va, rsize, roff = struct.unpack("<IIII", f.read(16))
        sections.append((sec_name, va, roff, vsize))
        print(f"Sec #{i+1}: {sec_name} -> VA: 0x{va:X}, RawOff: 0x{roff:X}, Size: 0x{vsize:X}")

# Section 4:
sec4 = sections[3]
# hos_oot_protect_hearts -> Val: 0x8A580D0, Sec: 4
rva_protect = sec4[1] + 0x8A580D0
foff_protect = sec4[2] + 0x8A580D0
print(f"hos_oot_protect_hearts RVA: 0x{rva_protect:X}, FileOffset: 0x{foff_protect:X}")

# hos_oot_live_action -> Val: 0x8A585C8, Sec: 4
rva_action = sec4[1] + 0x8A585C8
print(f"hos_oot_live_action RVA: 0x{rva_action:X}")

# Disassemble hos_oot_hearts_enabled at Val 0x1965F5A0 (Sec 1)
sec1 = sections[0]
foff_hearts = sec1[2] + 0x1965F5A0
f.seek(foff_hearts)
code_hearts = f.read(32)
print("hos_oot_hearts_enabled code:", code_hearts.hex())

# Disassemble hos_oot_is_player at Val 0x1965F5D0 (Sec 1)
foff_player = sec1[2] + 0x1965F5D0
f.seek(foff_player)
code_player = f.read(32)
print("hos_oot_is_player code:", code_player.hex())
