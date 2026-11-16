with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

import re
pos = 0x1a346925
snippet = data[pos-500:pos+1500]
strings = re.findall(rb"[\x20-\x7e]{3,}", snippet)
for s in strings:
    print("  String:", s.decode("latin1"))
