"""Independent demonstration website for the traditional row-oriented ETL baseline.
Run: python traditional_app.py. No database writes are performed.
"""
import csv
from functools import lru_cache
from pathlib import Path
from flask import Flask, render_template, request
from benchmarks.compare_etl import DATA, load_dimensions, traditional_etl
from evaluation_data import get_evaluation

app = Flask(__name__)

@lru_cache(maxsize=1)
def baseline_data():
    products, stores = load_dimensions()
    path = DATA / 'transactions.csv'
    with path.open(newline='', encoding='utf-8-sig') as f:
        count = sum(1 for _ in csv.DictReader(f))
    result, processed = traditional_etl(count, products, stores)
    return result, processed

@app.context_processor
def common():
    return {'site_name':'Traditional ETL', 'site_tag':'Sequential Python baseline', 'other_url':'http://127.0.0.1:5000', 'system':'traditional'}

@app.route('/')
def home():
    result, n=baseline_data()
    cats=result['sales_summary']; stores=result['store_summary']; daily=result['daily_sales']
    return render_template('baseline/home.html', active='home', count=n, categories=len(cats), stores=len(stores), days=len(daily), revenue=sum(r[-3] for r in cats)/100, top_categories=sorted(cats,key=lambda r:r[-3],reverse=True)[:6], eval=get_evaluation())

@app.route('/pipeline')
def pipeline():
    return render_template('baseline/pipeline.html',active='pipeline')

@app.route('/transactions')
def transactions():
    try:
        size = min(max(int(request.args.get('limit', 30)), 1), 100)
    except (TypeError, ValueError):
        size = 30
    with (DATA/'transactions.csv').open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        rows=[row for i,row in enumerate(reader) if i<size]
    return render_template('baseline/transactions.html',active='transactions',rows=rows,limit=size)

@app.route('/analytics')
def analytics():
    result,_=baseline_data()
    return render_template('baseline/analytics.html',active='analytics',categories=sorted(result['sales_summary'],key=lambda r:r[-3],reverse=True),stores=sorted(result['store_summary'],key=lambda r:r[-3],reverse=True),days=result['daily_sales'][-20:])

@app.route('/evaluation')
def evaluation():
    return render_template('baseline/evaluation.html',active='evaluation',evaluation=get_evaluation())

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5001,debug=False)
