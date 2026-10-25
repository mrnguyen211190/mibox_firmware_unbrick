import os, sys, runpy
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
script = os.path.join(sys.argv[2], 'ubt.py')
sys.argv = [script] + sys.argv[3:]
runpy.run_path(script, run_name='__main__')
