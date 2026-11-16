with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    f.seek(0x400 + 0x1965FE40)
    code = f.read(2048)

for off in (0x3A6, 0x48F, 0x71C):
    snippet = code[max(0, off-20):min(len(code), off+20)]
    print(f"Around 0x{off:X}: {snippet.hex()}")
