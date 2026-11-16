import pefile

pe = pefile.PE(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot_vk.dll")
sec1 = pe.sections[0]
with open(r"C:\Users\Antonio Garcia\Games\Hookshot\bin\hookshot_vk.dll", "rb") as f:
    data = f.read()

# Val 0x30E480 in Sec 1:
foff = sec1.PointerToRawData + 0x30E480
code = data[foff:foff+128]
print("cheat_value hex:", code.hex())
