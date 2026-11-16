with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    f.seek(0x400 + 0x1965FE40 + 0x480)
    code = f.read(96)
    print("Code at 0x480:", code.hex())
