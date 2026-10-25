# Bring the box from ROM (IPL) to u-boot burning mode (TPL) using pyamlboot's optimus steps.
# USB DDR/UBOOT items are synthesized from the image's bootloader partition. RAM only.
import sys, io, logging, argparse
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
from pyamlboot.amlimage import AmlImagePack
from pyamlboot import optimus as o
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)-7s %(message)s', datefmt='%H:%M:%S')

class Item:
    def __init__(self, sub, data): self._s, self._b = sub, io.BytesIO(data); self._n = len(data)
    def seek(self, *a): return self._b.seek(*a)
    def read(self, n=-1): return self._b.read(n)
    def size(self): return self._n
    def sub_type(self): return self._s

img = AmlImagePack(open(sys.argv[3], 'rb'))
platform = bl = None
for it in img.items():
    if (it.main_type(), it.sub_type()) == ('conf', 'platform'):
        platform = o.Platform(it.read().decode())
    if (it.main_type(), it.sub_type()) == ('PARTITION', 'bootloader'):
        it.seek(0, 0); bl = it.read()
ddr, tpl = bl[:0xC000], bl[0xC000:]
items = {('USB', 'DDR'): Item('DDR', ddr), ('USB', 'DDR_ENC'): Item('DDR_ENC', ddr),
         ('USB', 'UBOOT'): Item('UBOOT', tpl), ('USB', 'UBOOT_ENC'): Item('UBOOT_ENC', tpl)}
pwd = open(sys.argv[4], 'rb')
sd = o.SharedData()
steps = [o.BurnStepCheckPassword(sd, password_fd=pwd),
         o.BurnStepBoardIsSecure(sd, platform=platform),
         o.BurnStepDownloadSPL(sd, images=items, platform=platform, password_fd=pwd),
         o.BurnStepDownloadUboot(sd, images=items, platform=platform)]
o.do_burn(steps)
dev = o.wait_device(timeout=20)
print("FINAL:", o.SocId(dev.identify()))
