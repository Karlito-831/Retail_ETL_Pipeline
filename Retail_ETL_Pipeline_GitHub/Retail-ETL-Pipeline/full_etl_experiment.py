"""Isolated PostgreSQL ETL experiment. Does not modify public schema."""
import argparse, csv, gc, os, statistics, threading, time
from datetime import datetime
from pathlib import Path
import pandas as pd
import psutil
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'raw'
REPORTS = ROOT / 'reports'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--sizes',type=int,nargs='+',default=[1000,10000,100000])
    args=parser.parse_args()
    if args.repeats<1 or any(n<1 for n in args.sizes):parser.error('Invalid sizes or repetitions')
    for name in ('transactions','products','stores'):
        if not (DATA/f'{name}.csv').is_file():parser.error(f'Missing {DATA/name}.csv')
    from scripts.database import get_engine
    engine=get_engine()
    schema='etl_eval_'+datetime.now().strftime('%Y%m%d_%H%M%S')
    # Refuse to use any pre-existing schema. No DROP statements are issued.
    with engine.begin() as conn:
        if conn.execute(text('SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name=:s)'),{'s':schema}).scalar():
            raise RuntimeError('Experiment schema already exists; retry after one second')
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    print('Isolated experiment schema:',schema)
    print('Existing public/application tables will NOT be modified.')
    products=pd.read_csv(DATA/'products.csv')
    stores=pd.read_csv(DATA/'stores.csv')
    tx_path=DATA/'transactions.csv'
    proc=psutil.Process(os.getpid())
    rows=[]
    REPORTS.mkdir(exist_ok=True)
    for n in args.sizes:
        for rep in range(1,args.repeats+1):
            gc.collect()
            baseline=proc.memory_info().rss
            peak=[baseline]
            stop=threading.Event()
            def monitor():
                while not stop.wait(0.01):
                    try:peak[0]=max(peak[0],proc.memory_info().rss)
                    except psutil.Error:break
            sampler=threading.Thread(target=monitor,daemon=True)
            cpu0=proc.cpu_times()
            sampler.start()
            t0=time.perf_counter()
            try:
                a=time.perf_counter()
                tx=pd.read_csv(tx_path,nrows=n)
                if len(tx)!=n:raise ValueError(f'Only {len(tx)} rows available; expected {n}')
                # Source CSV has no transaction_id; PostgreSQL's SERIAL key is generated on load.
                # Use a deterministic row identifier for equivalent count aggregations.
                if 'transaction_id' not in tx.columns:
                    tx.insert(0,'transaction_id',range(1,len(tx)+1))
                extraction=time.perf_counter()-a
                a=time.perf_counter()
                # Match the analytical summaries used in scripts/transform.py.
                prod=products.copy();prod.insert(0,'product_id',range(1,len(prod)+1)) if 'product_id' not in prod else None
                st=stores.copy();st.insert(0,'store_id',range(1,len(st)+1)) if 'store_id' not in st else None
                sales=tx.merge(prod,on='product_id',how='left',validate='many_to_one')
                loc=tx.merge(st,on='store_id',how='left',validate='many_to_one')
                if sales['category'].isna().any() or loc['store_name'].isna().any():raise ValueError('Unmatched foreign key')
                summary=sales.groupby('category',as_index=False).agg(Total_Revenue=('total_amount','sum'),Total_Orders=('transaction_id','count'),Average_Order_Value=('total_amount','mean'))
                by_store=loc.groupby(['store_id','store_name','city'],as_index=False).agg(Revenue=('total_amount','sum'),Orders=('transaction_id','count'),Average_Order_Value=('total_amount','mean'))
                tx['transaction_date']=pd.to_datetime(tx['transaction_date'])
                daily=tx.groupby(tx['transaction_date'].dt.date).agg(Revenue=('total_amount','sum'),Orders=('transaction_id','count')).reset_index()
                transform=time.perf_counter()-a
                a=time.perf_counter()
                # All writes are restricted to this uniquely created schema.
                with engine.begin() as conn:
                    tx.to_sql('transactions',conn,schema=schema,if_exists='replace',index=False)
                    summary.to_sql('sales_summary',conn,schema=schema,if_exists='replace',index=False)
                    by_store.to_sql('store_summary',conn,schema=schema,if_exists='replace',index=False)
                    daily.to_sql('daily_sales',conn,schema=schema,if_exists='replace',index=False)
                loading=time.perf_counter()-a
                total=time.perf_counter()-t0
            finally:
                stop.set();sampler.join()
            cpu1=proc.cpu_times()
            peak[0]=max(peak[0],proc.memory_info().rss)
            cpu=(cpu1.user+cpu1.system)-(cpu0.user+cpu0.system)
            row=dict(timestamp=datetime.now().astimezone().isoformat(),schema=schema,transactions=n,repeat=rep,extract_seconds=extraction,transform_seconds=transform,load_seconds=loading,total_seconds=total,throughput_records_per_sec=n/total,cpu_seconds=cpu,cpu_core_equivalent_percent=100*cpu/total,peak_rss_mib=peak[0]/1048576,rss_peak_above_start_mib=(peak[0]-baseline)/1048576,summary_rows=len(summary),store_rows=len(by_store),daily_rows=len(daily))
            rows.append(row)
            print(f'{n:>7,} run {rep}: E={extraction:.3f}s T={transform:.3f}s L={loading:.3f}s TOTAL={total:.3f}s')
    path=REPORTS/'full_postgres_etl_results.csv'
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary_path=REPORTS/'full_postgres_etl_summary.csv'
    fields=['extract_seconds','transform_seconds','load_seconds','total_seconds','throughput_records_per_sec','cpu_seconds','peak_rss_mib']
    with summary_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['transactions','runs']+[f'{k}_mean' for k in fields]+['total_seconds_std'])
        for n in args.sizes:
            subset=[r for r in rows if r['transactions']==n]
            w.writerow([n,len(subset)]+[statistics.mean(r[k] for r in subset) for k in fields]+[statistics.stdev(r['total_seconds'] for r in subset) if len(subset)>1 else 0])
    print('\nSaved:',path,'\nSaved:',summary_path)
    print('The experiment schema was retained for verification:',schema)
    print('Do not drop it until results have been checked.')
if __name__=='__main__':main()
