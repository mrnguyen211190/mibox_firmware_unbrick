# Continue from BL2 stage (identify x-x-0-8): load FIP params + TPL with control writes, then run.
import sys, time, os
here = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, here)
import usb.backend.libusb0 as b0
import pyamlboot_lib as pl
be = b0.get_backend(find_library=lambda x: r"C:\Windows\System32\libusb0.dll")
DDR_LOAD, BL2_PARAMS, UBOOT_LOAD = 0xd9000000, 0xd900c000, 0x200c000
f = lambda n: open(os.path.join(here, n), 'rb').read()
dev = pl.AmlogicSoC(usb_backend=be, timeout=15)
s = [ord(c) for c in dev.identify()]; print("identify:", "-".join(map(str, s)), flush=True)
if s[3] != 8:
    sys.exit("not in BL2 stage")
t = time.time()
dev.writeMemory(DDR_LOAD, f('u-boot.bin.usb.bl2')); print("BL2 rewritten", flush=True)
dev.writeMemory(BL2_PARAMS, f('usbbl2runpara_runfipimg.bin')); print("FIP params written", flush=True)
tpl = f('u-boot.bin.usb.tpl'); tpl += b'\0' * (-len(tpl) % 64)
for off in range(0, len(tpl), 64 * 512):
    dev.writeMemory(UBOOT_LOAD + off, tpl[off:off + 64 * 512])
    print("TPL %d/%d" % (min(off + 64 * 512, len(tpl)), len(tpl)), flush=True)
print("written in %.0fs, run u-boot" % (time.time() - t), flush=True)
dev.run(BL2_PARAMS)
print("done", flush=True)
