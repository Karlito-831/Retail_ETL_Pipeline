"""Read measured results; never fabricate benchmark measurements."""
import csv
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev
BASE = Path(__file__).resolve().parent

def get_evaluation():
    # Prefer the full-precision files generated on the user's computer.
    measured = BASE / 'reports' / 'comparative_results.csv'
    imported = BASE / 'reports' / 'observed_terminal_timings.csv'
    source = measured if measured.exists() else imported
    if not source.exists():
        return {'rows': [], 'source': 'No benchmark results yet', 'full_precision': False}
    with source.open(newline='', encoding='utf-8-sig') as f:
        records = list(csv.DictReader(f))
    grouped = defaultdict(list)
    for row in records:
        grouped[(int(row['dataset_size']), row['implementation'])].append(float(row['seconds']))
    rows=[]
    for n in sorted(set(k[0] for k in grouped)):
        t=grouped.get((n,'traditional'),[]); a=grouped.get((n,'artifact'),[])
        if not t or not a: continue
        tm,am=mean(t),mean(a)
        rows.append({'size':n,'traditional':tm,'artifact':am,'traditional_std':stdev(t) if len(t)>1 else 0,'artifact_std':stdev(a) if len(a)>1 else 0,'traditional_throughput':n/tm,'artifact_throughput':n/am,'reduction':100*(tm-am)/tm,'speedup':tm/am,'repeats':min(len(t),len(a)),'winner':'Proposed artifact' if am<tm else 'Traditional baseline'})
    return {'rows':rows,'source':'Original full-precision benchmark CSV' if source==measured else 'Terminal-observed timings (rounded to 4 decimals)', 'full_precision':source==measured}
