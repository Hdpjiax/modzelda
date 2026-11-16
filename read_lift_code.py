with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    # sec1 RawOff = 0x400
    foff_hearts = 0x400 + 0x1965F5A0
    f.seek(foff_hearts)
    code_hearts = f.read(32)
    print("hos_oot_hearts_enabled code:", code_hearts.hex())

    foff_player = 0x400 + 0x1965F5D0
    f.seek(foff_player)
    code_player = f.read(32)
    print("hos_oot_is_player code:", code_player.hex())

    # Val 0x1965FE40: hos_oot_lift_player
    foff_lift = 0x400 + 0x1965FE40
    f.seek(foff_lift)
    code_lift = f.read(64)
    print("hos_oot_lift_player code:", code_lift.hex())
