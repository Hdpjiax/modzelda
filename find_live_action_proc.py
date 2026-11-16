with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

# RVA of hos_oot_live_action is 0x232C35C8
# In sec4, RawOff = 0x1A868200
# File offset = 0x1A868200 + 0x8A585C8 = 0x232C07C8
# Let's search for instructions in sec1 that reference 0x140000000 + 0x232C35C8
target_va = 0x140000000 + 0x232C35C8
sec1_raw = 0x400
sec1_va = 0x140000000 + 0x1000
sec1_size = 0x19F19376

import struct
f_pos = 0x400
# We can read in chunks of 16MB to find disp32 targeting target_va
chunk_size = 16 * 1024 * 1024
for c in range(0, sec1_size, chunk_size):
    read_len = min(chunk_size, sec1_size - c)
    chunk = data[sec1_raw + c : sec1_raw + c + read_len]
    for i in range(len(chunk)-7):
        disp = struct.unpack_from("<i", chunk, i+3)[0]
        insn_va = sec1_va + c + i
        if insn_va + 7 + disp == target_va:
            print(f"hos_oot_live_action referenced at 0x{insn_va:X}")
            print("Bytes:", chunk[i:i+32].hex())
