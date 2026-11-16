with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

pos = data.find(b"HOS_INPUT_LIVE")
print("HOS_INPUT_LIVE pos in hookshot.exe:", hex(pos))

# Search for "!cheat" or "!teleport"
pos_cheat = data.find(b"!cheat")
print("!cheat pos in hookshot.exe:", hex(pos_cheat))
pos_tele = data.find(b"!teleport")
print("!teleport pos in hookshot.exe:", hex(pos_tele))
