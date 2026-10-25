# Run pyamlboot's optimus burn with USB DDR/UBOOT items synthesized from the bootloader partition.
import sys, io, logging, argparse
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
from pyamlboot.amlimage import AmlImagePack
from pyamlboot import optimus as o
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)-7s %(message)s', datefmt='%H:%M:%S')

class Item:
    def __init__(self, sub, data): self._s, self._b, self._n = sub, io.BytesIO(data), len(data)
    def main_type(self): return 'USB'
    def sub_type(self): return self._s
    def seek(self, *a): return self._b.seek(*a)
    def read(self, n=-1): return self._b.read(n)
    def size(self): return self._n

class Img:
    def __init__(self, img):
        self._img = img
        bl = next(i for i in img.items() if (i.main_type(), i.sub_type()) == ('PARTITION', 'bootloader'))
        bl.seek(0, 0); d = bl.read()
        self._extra = [Item('DDR', d[:0xC000]), Item('DDR_ENC', d[:0xC000]),
                       Item('UBOOT', d[0xC000:]), Item('UBOOT_ENC', d[0xC000:])]
    def items(self): return list(self._img.items()) + self._extra

class WipeFormat:
    def __init__(self, v): self.value = v

args = argparse.Namespace(img=None, reset=True, no_erase_bootloader=True,
                          wipe=WipeFormat(1), password=open(sys.argv[4], 'rb'))
img = Img(AmlImagePack(open(sys.argv[3], 'rb')))
sd = o.SharedData()
steps = o.get_burn_steps(args, sd, img)
di = next(i for i, st in enumerate(steps) if getattr(st, '_cmd', '').startswith('disk_initial'))
dtb = next(i for i, st in enumerate(steps) if getattr(st, '_path', None) == 'dtb')
steps.insert(di, steps.pop(dtb))
print('order:', [getattr(st, '_title', '?') for st in steps])
o.do_burn(steps)
print("BURN FINISHED")
