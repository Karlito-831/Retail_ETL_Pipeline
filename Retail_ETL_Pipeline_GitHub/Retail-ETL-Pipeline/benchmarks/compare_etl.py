"""Reproducible comparison: row-oriented Python vs Pandas, same CSV and analytical outputs.
Runs in memory; no writes to the user's PostgreSQL database.
"""
import argparse
import csv
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import threading
import time
from datetime import datetime
from collections import defaultdict

import pandas as pd
import psutil

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'data' / 'raw'
REPORTS = BASE / 'reports'
FIELDS = ('category', 'revenue', 'orders', 'average_order_value')


def load_dimensions():
    # Source CSV has no ID columns; the project's generator assigns 1-based IDs.
    with (DATA / 'products.csv').open(newline='', encoding='utf-8-sig') as f:
        products = {i: r['category'] for i, r in enumerate(csv.DictReader(f), 1)}
    with (DATA / 'stores.csv').open(newline='', encoding='utf-8-sig') as f:
        stores = {i: (r['store_name'], r['city']) for i, r in enumerate(csv.DictReader(f), 1)}
    return products, stores


def traditional_etl(n, products, stores):
    category = defaultdict(lambda: [0, 0])
    store = defaultdict(lambda: [0, 0])
    daily = defaultdict(lambda: [0, 0])
    count = 0
    with (DATA / 'transactions.csv').open(newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if count == n: break
            product_id = int(row['product_id'])
            store_id = int(row['store_id'])
            if product_id not in products or store_id not in stores:
                raise ValueError('Unmatched product or store ID')
            # Integer cents avoids floating-point aggregation discrepancies.
            cents = round(float(row['total_amount']) * 100)
            day = datetime.fromisoformat(row['transaction_date']).date().isoformat()
            c = category[products[product_id]];c[0] += cents;c[1] += 1
            s = store[(store_id, *stores[store_id])];s[0] += cents;s[1] += 1
            d = daily[day];d[0] += cents;d[1] += 1
            count += 1
    if count != n:raise ValueError(f'Expected {n} records, got {count}')
    return canonical(category, store, daily), count


def artifact_etl(n, products, stores):
    # Vectorised operations mirror scripts/transform.py: joins + groupby.
    tx = pd.read_csv(DATA / 'transactions.csv', nrows=n)
    if len(tx) != n:raise ValueError(f'Expected {n} records, got {len(tx)}')
    tx['cents'] = (tx['total_amount'] * 100).round().astype('int64')
    prod = pd.DataFrame({'product_id':list(products), 'category':list(products.values())})
    store_rows = [(k, *v) for k,v in stores.items()]
    st = pd.DataFrame(store_rows, columns=['store_id','store_name','city'])
    sales = tx.merge(prod, on='product_id', how='left', validate='many_to_one')
    location = tx.merge(st, on='store_id', how='left', validate='many_to_one')
    if sales['category'].isna().any() or location['store_name'].isna().any():
        raise ValueError('Unmatched dimension key')
    a = sales.groupby('category', sort=True)['cents'].agg(['sum','count'])
    b = location.groupby(['store_id','store_name','city'], sort=True)['cents'].agg(['sum','count'])
    days = pd.to_datetime(tx['transaction_date']).dt.strftime('%Y-%m-%d')
    c = tx.groupby(days, sort=True)['cents'].agg(['sum','count'])
    return canonical(
        {str(k):[int(v['sum']),int(v['count'])] for k,v in a.iterrows()},
        {(int(k[0]),str(k[1]),str(k[2])):[int(v['sum']),int(v['count'])] for k,v in b.iterrows()},
        {str(k):[int(v['sum']),int(v['count'])] for k,v in c.iterrows()}),len(tx)


def canonical(category, store, daily):
    # A canonical format ensures equivalent totals, counts, and averages.
    def row(key, v):
        return [*key, int(v[0]), int(v[1]), round(v[0]/(100*v[1]), 6)]
    return {
        'sales_summary': sorted([row([k],v) for k,v in category.items()]),
        'store_summary': sorted([row(list(k),v) for k,v in store.items()]),
        'daily_sales': sorted([row([k],v) for k,v in daily.items()]),
    }


def digest(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True, separators=(',',':')).encode()).hexdigest()


def measured_run(fn, n, products, stores):
    gc.collect()
    process=psutil.Process(os.getpid())
    cpu_before=process.cpu_times()
    rss_before=process.memory_info().rss
    peak=[rss_before]
    stop=threading.Event()
    def sampler():
        while not stop.wait(.01):
            try:peak[0]=max(peak[0],process.memory_info().rss)
            except psutil.Error:break
    worker=threading.Thread(target=sampler, daemon=True)
    worker.start()
    t0=time.perf_counter()
    try:
        result, count=fn(n, products, stores)
        elapsed=time.perf_counter()-t0
    finally:
        stop.set();worker.join()
    cpu_after=process.cpu_times()
    peak[0]=max(peak[0],process.memory_info().rss)
    cpu_seconds=(cpu_after.user+cpu_after.system)-(cpu_before.user+cpu_before.system)
    return {'seconds':elapsed,'throughput_records_per_sec':count/elapsed,
            'cpu_seconds':cpu_seconds,'cpu_core_equivalent_percent':100*cpu_seconds/elapsed,
            'peak_rss_mb':peak[0]/1048576,'rss_increase_mb':(peak[0]-rss_before)/1048576,
            'result':result,'sha256':digest(result)}


def main():
    parser=argparse.ArgumentParser(description='Traditional vs Pandas ETL benchmark')
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--sizes',type=int,nargs='+',default=[1000,10000,100000])
    args=parser.parse_args()
    if args.repeats<1 or any(n<1 for n in args.sizes):parser.error('Sizes and repeats must be positive')
    REPORTS.mkdir(exist_ok=True)
    products,stores=load_dimensions()
    # Correctness test, separate from timed experiments.
    print('Validating equivalent outputs...')
    for n in args.sizes:
        a,_=traditional_etl(n,products,stores)
        b,_=artifact_etl(n,products,stores)
        if a!=b:raise AssertionError(f'Outputs differ at {n:,} rows. Benchmark aborted.')
        print(f'  {n:,} records: PASS ({len(a["sales_summary"])} categories, {len(a["store_summary"])} stores, {len(a["daily_sales"])} days)')
    rows=[]
    stamp=datetime.now().astimezone().isoformat()
    # Alternate order each repeat to mitigate systematic warm-cache bias.
    for n in args.sizes:
        for repeat in range(1,args.repeats+1):
            variants=[('traditional',traditional_etl),('artifact',artifact_etl)]
            if repeat%2==0:variants.reverse()
            for name,fn in variants:
                metrics=measured_run(fn,n,products,stores)
                row={'timestamp':stamp,'dataset_size':n,'repeat':repeat,'implementation':name,
                     'correctness':'PASS',**{k:v for k,v in metrics.items() if k!='result'}}
                rows.append(row)
                print(f'{n:>7,} | run {repeat} | {name:<11} | {row["seconds"]:.4f}s | {row["throughput_records_per_sec"]:,.0f} rec/s')
    path=REPORTS/'comparative_results.csv'
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary=[]
    for n in args.sizes:
        grouped={name:[r for r in rows if r['dataset_size']==n and r['implementation']==name] for name in ('traditional','artifact')}
        t=statistics.mean(r['seconds'] for r in grouped['traditional'])
        a=statistics.mean(r['seconds'] for r in grouped['artifact'])
        for name,group in grouped.items():
            times=[r['seconds'] for r in group]
            summary.append({'dataset_size':n,'implementation':name,'runs':len(group),
                            'mean_seconds':statistics.mean(times),
                            'std_seconds':statistics.stdev(times) if len(times)>1 else 0,
                            'median_seconds':statistics.median(times),
                            'mean_throughput':statistics.mean(r['throughput_records_per_sec'] for r in group),
                            'mean_cpu_seconds':statistics.mean(r['cpu_seconds'] for r in group),
                            'mean_peak_rss_mb':statistics.mean(r['peak_rss_mb'] for r in group),
                            'time_reduction_vs_baseline_pct':(t-a)/t*100 if name=='artifact' else 0,
                            'speedup_vs_baseline':t/a if name=='artifact' else 1})
    path2=REPORTS/'comparative_summary.csv'
    with path2.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(9,5))
        for name in ('traditional','artifact'):
            subset=[r for r in summary if r['implementation']==name]
            ax.plot([str(r['dataset_size']) for r in subset],[r['mean_seconds'] for r in subset],marker='o',label=name)
        ax.set(xlabel='Transactions',ylabel='Mean execution time (seconds)',title='ETL implementation comparison')
        ax.legend();fig.tight_layout();fig.savefig(REPORTS/'comparative_execution_time.png',dpi=160);plt.close(fig)
    except ImportError:
        print('matplotlib not installed; chart skipped')
    print(f'\nSaved {path}\nSaved {path2}')

if __name__=='__main__':main()
