# Load the image's bootloader into RAM via Amlogic ROM USB (pyamlboot GX flow). RAM only.
import sys, time, os
here = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, here)
import usb.backend.libusb0 as b0
import pyamlboot_lib as pl
be = b0.get_backend(find_library=lambda x: r"C:\Windows\System32\libusb0.dll")
pwd = open(sys.argv[2], 'rb').read()
DDR_LOAD, BL2_PARAMS, UBOOT_LOAD = 0xd9000000, 0xd900c000, 0x200c000
f = lambda n: open(os.path.join(here, n), 'rb').read()
dev = None

def soc():
    global dev
    if dev is not None:
        dev.disposeDevice()
    dev = pl.AmlogicSoC(usb_backend=be, timeout=15)
    s = [ord(c) for c in dev.identify()]
    print("identify:", "-".join(map(str, s)), flush=True)
    if len(s) > 5 and s[4] == 1 and s[5] == 0:
        dev.dev.ctrl_transfer(0x40, 0x35, 0, 0, pwd)
        s = [ord(c) for c in dev.identify()]
        print("password sent ->", "-".join(map(str, s)), flush=True)
    return s

# init_ddr
s = soc()
print("1. write BL2 + ddrinit params, run BL2", flush=True)
dev.writeMemory(DDR_LOAD, f('u-boot.bin.usb.bl2'))
dev.writeMemory(BL2_PARAMS, f('usbbl2runpara_ddrinit.bin'))
dev.run(DDR_LOAD)
time.sleep(1)
s = soc()
if s[3] == 8:
    print("   BL2 stage, run ddr init", flush=True)
    dev.run(BL2_PARAMS)
    time.sleep(1)
    s2 = soc()
# load_uboot
print("2. write BL2 + FIP params + TPL (%d bytes)" % len(f('u-boot.bin.usb.tpl')), flush=True)
dev.writeLargeMemory(DDR_LOAD, f('u-boot.bin.usb.bl2'), 64)
dev.writeLargeMemory(BL2_PARAMS, f('usbbl2runpara_runfipimg.bin'), 48)
dev.writeLargeMemory(UBOOT_LOAD, f('u-boot.bin.usb.tpl'), 64, True)
print("3. run u-boot", flush=True)
dev.run(BL2_PARAMS if s[3] == 8 else DDR_LOAD)
print("done", flush=True)
