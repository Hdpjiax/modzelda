with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    foff_lift = 0x400 + 0x1965FE40
    f.seek(foff_lift)
    code = f.read(512)
    # search for immediate constants or offsets
    print("Code len:", len(code))
    # print first 128 bytes
    print(code[:128].hex())
