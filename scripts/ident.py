import sys
sys.path.insert(0, sys.argv[1])
import usb.core, usb.backend.libusb0 as b0
be = b0.get_backend(find_library=lambda x: r"C:\Windows\System32\libusb0.dll")
dev = usb.core.find(idVendor=0x1b8e, idProduct=0xc003, backend=be)
if dev is None:
    print("device not found"); sys.exit(1)
print("bcdDevice=%#06x" % dev.bcdDevice)
ret = dev.ctrl_transfer(0xc0, 0x20, 0, 0, 8)   # REQ_IDENTIFY_HOST (read-only)
print("identify:", "-".join(str(x) for x in ret))
