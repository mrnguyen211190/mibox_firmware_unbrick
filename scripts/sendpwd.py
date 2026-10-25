import sys
sys.path.insert(0, sys.argv[1])
import usb.core, usb.backend.libusb0 as b0
be = b0.get_backend(find_library=lambda x: r"C:\Windows\System32\libusb0.dll")
dev = usb.core.find(idVendor=0x1b8e, idProduct=0xc003, backend=be)
ident = lambda: "-".join(str(x) for x in dev.ctrl_transfer(0xc0, 0x20, 0, 0, 8))
before = ident(); print("before:", before)
if before.split("-")[4:6] != ["1", "0"]:
    print("state changed, not sending"); sys.exit(2)
pwd = open(sys.argv[2], "rb").read()
dev.ctrl_transfer(0x40, 0x35, 0, 0, pwd)          # REQ_PASSWORD, one attempt
print("after: ", ident())
