# Search hookshot.exe for strings related to health / hearts
with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

import re
# In OoT, max health is 0x140 (320), starting is 0x30 (48)
# Let's search for "protect_hearts" or "heart_protection"
for term in [b"protect_hearts", b"heart_protection", b"Protect hearts"]:
    pos = 0
    while True:
        idx = data.find(term, pos)
        if idx == -1: break
        print(f"Found {term.decode()} in hookshot.exe at 0x{idx:X}")
        pos = idx + len(term)
