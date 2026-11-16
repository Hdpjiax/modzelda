with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    f.seek(0x400 + 0x1965FE40)
    code = f.read(2048)

# Find all memory writes [reg + offset]
# Or search for 320 (0x140) or 20 or 96 (0x60)
import struct
for i in range(len(code)-4):
    u16_val = struct.unpack_from("<H", code, i)[0]
    if u16_val in (320, 20, 96, 48):
        print(f"Constant {u16_val} at lift+0x{i:X}")
