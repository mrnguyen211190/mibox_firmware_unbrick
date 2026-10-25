import struct, sys
f = open(sys.argv[1], 'rb'); h = f.read(64); n = struct.unpack('<I', h[24:28])[0]
items = []
for i in range(n):
    it = f.read(576); iid, ft, cur, off, sz = struct.unpack('<IIQQQ', it[:32])
    items.append((it[32:288].split(b'\0')[0].decode(), it[288:544].split(b'\0')[0].decode(), off, sz))
for main, sub, off, sz in items:
    if (main, sub) in [('conf', 'platform')] or sub == 'bootloader' and main == 'PARTITION':
        f.seek(off); d = f.read(sz)
        if main == 'conf': print(d.decode(errors='replace'))
        else:
            open(sys.argv[2] + '/bootloader.img', 'wb').write(d); print('bootloader saved', len(d), d[:16].hex(), d[0x10:0x20].hex())
