with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    # sec1 raw = 0x400
    # hos_oot_hearts_enabled = 0x400 + 0x1965F5A0
    f.seek(0x400 + 0x1965F5A0)
    code = f.read(64)
    print("Code hex:", code.hex())
    # 48 83 ec 28 : sub rsp, 0x28
    # b9 20 00 00 00 : mov ecx, 0x20
    # ba ff ff ff ff : mov edx, -1
    # e8 dd df 06 00 : call ...
    # 85 c0 : test eax, eax
    # 79 06 : jns ...
    # 8b 05 13 2b c6 09 : mov eax, [rip + 0x9c62b13]
    # rip = 0x140000000 + 0x1000 + 0x1965F5A0 + 26 = 0x1596605BA
    # Target = 0x1596605BA + 0x9c62b13 = 0x1632C30CD
    # RVA = 0x1632C30CD - 0x140000000 = 0x232C30CD !
    # NEAR hos_oot_protect_hearts at 0x232C30D0 !
