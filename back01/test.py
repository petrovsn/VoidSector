import psutil
from pprint import pprint as pp
pp([
     (p.pid, p.info['name'], sum(p.info['cpu_times'])) 
     for p in sorted(psutil.process_iter(['name', 'cpu_times']), 
                     key=lambda p: sum(p.info['cpu_times'][:2]))
    ][-10:])