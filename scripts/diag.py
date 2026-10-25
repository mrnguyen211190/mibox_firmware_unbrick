import sys, time
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
from pyamlboot import optimus as o
dev = o.wait_device()
print("identify:", o.SocId(dev.identify()))
def cmd(c, t=10000):
    try:
        dev.bulkCmd(c, read_status=False, timeout=t)
        r = bytes(dev.bulkCmdStat(timeout=t)).rstrip(b'\0')
    except Exception as e:
        r = repr(e).encode()
    print(f"{c!r:32} -> {r[:120]!r}", flush=True)
for c in sys.argv[3:]:
    cmd(c)
