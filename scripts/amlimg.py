import struct, sys, zlib
f = open(sys.argv[1], 'rb'); h = f.read(64)
crc, ver, magic, size, align, n = struct.unpack('<IIIQII', h[:28])
print(f"ver={ver} magic={magic:#x} size={size} items={n}")
for i in range(n):
    it = f.read(576)
    iid, ft, cur, off, sz = struct.unpack('<IIQQQ', it[:32])
    main = it[32:288].split(b'\0')[0].decode(); sub = it[288:544].split(b'\0')[0].decode()
    print(f"{main:8} {sub:24} {sz:>12}")
# verify CRC32 over file from offset 4
f.seek(4); c = 0
while (b := f.read(1 << 22)): c = zlib.crc32(b, c)
# Amlogic uses zlib CRC32 without the final XOR
c = (c ^ 0xffffffff) & 0xffffffff
print("crc stored", hex(crc), "computed", hex(c), "OK" if crc == c else "MISMATCH")
