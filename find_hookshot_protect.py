with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

import re
pos = data.find(b"HOS_OOT_PROTECT_HEARTS")
print("Pos of HOS_OOT_PROTECT_HEARTS in hookshot.exe:", hex(pos))

# In hookshot.exe, let's find references to this string offset
# ImageBase = 0x140000000 or let's check with pefile
import pefile
pe = pefile.PE(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe")
print("Hookshot.exe ImageBase:", hex(pe.OPTIONAL_HEADER.ImageBase))
sec = [s for s in pe.sections if s.PointerToRawData <= pos < s.PointerToRawData + s.SizeOfRawData][0]
str_va = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress + (pos - sec.PointerToRawData)
print(f"HOS_OOT_PROTECT_HEARTS string VA: 0x{str_va:X}")
