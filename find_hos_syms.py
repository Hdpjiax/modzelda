with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot.exe", "rb") as f:
    data = f.read()

import re
pos = data.find(b"hos_oot_protect_hearts")
print("Pos:", hex(pos))

# In COFF / PE symbol table
import struct
pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
sym_table_ptr = struct.unpack_from("<I", data, pe_offset + 12)[0]
num_symbols = struct.unpack_from("<I", data, pe_offset + 16)[0]
str_table_ptr = sym_table_ptr + num_symbols * 18

print(f"Num symbols: {num_symbols}")
for i in range(num_symbols):
    offset = sym_table_ptr + i * 18
    name_bytes = data[offset:offset+8]
    val, sec_num, sym_type, s_class, num_aux = struct.unpack_from("<IhhBB", data, offset + 8)
    if name_bytes[:4] == b"\x00\x00\x00\x00":
        str_off = struct.unpack_from("<I", name_bytes, 4)[0]
        end = data.find(b"\x00", str_table_ptr + str_off)
        name = data[str_table_ptr + str_off:end].decode("latin1", "ignore")
    else:
        name = name_bytes.rstrip(b"\x00").decode("latin1", "ignore")
        
    if "hos_oot" in name or "protect_hearts" in name:
        print(f"Symbol: {name} -> Val: 0x{val:X}, Sec: {sec_num}")
