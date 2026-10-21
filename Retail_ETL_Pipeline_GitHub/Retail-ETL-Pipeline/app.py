from flask import Flask, render_template
from sqlalchemy import text
from scripts.database import get_engine
import plotly.express as px

app = Flask(__name__)

from evaluation_data import get_evaluation

@app.route("/evaluation")
def evaluation_dashboard():
    return render_template("baseline/evaluation.html", active="evaluation", evaluation=get_evaluation(), site_name="Proposed ETL Artifact", site_tag="Pandas-based analytical ETL", other_url="http://127.0.0.1:5001", system="artifact")


engine = get_engine()


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    with engine.connect() as conn:

        customers = conn.execute(
            text("SELECT COUNT(*) FROM customers")
        ).scalar()

        products = conn.execute(
            text("SELECT COUNT(*) FROM products")
        ).scalar()

        stores = conn.execute(
            text("SELECT COUNT(*) FROM stores")
        ).scalar()

        transactions = conn.execute(
            text("SELECT COUNT(*) FROM transactions")
        ).scalar()

        revenue = conn.execute(
            text("SELECT COALESCE(SUM(total_amount), 0) FROM transactions")
        ).scalar()

        avg_sale = conn.execute(
            text("SELECT COALESCE(AVG(total_amount), 0) FROM transactions")
        ).scalar()

        category_data = conn.execute(text("""
            SELECT
                p.category,
                SUM(t.total_amount) AS revenue
            FROM transactions t
            JOIN products p
                ON t.product_id = p.product_id
            GROUP BY p.category
            ORDER BY revenue DESC;
        """)).fetchall()

    categories = [row[0] for row in category_data]
    revenues = [float(row[1]) for row in category_data]

    fig = px.bar(
        x=categories,
        y=revenues,
        title="Revenue by Product Category",
        color=revenues,
        color_continuous_scale="Blues"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="white",
        margin=dict(l=20, r=20, t=60, b=20),
        height=500,
        title_x=0.5,
        coloraxis_showscale=False
    )

    chart = fig.to_html(full_html=False)

    return render_template(
        "index.html",
        customers=customers,
        products=products,
        stores=stores,
        transactions=transactions,
        revenue=round(float(revenue), 2),
        avg_sale=round(float(avg_sale), 2),
        chart=chart
    )


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/analytics")
def analytics():

    with engine.connect() as conn:

        category_data = conn.execute(text("""
            SELECT
                p.category,
                SUM(t.total_amount) AS revenue,
                COUNT(t.transaction_id) AS orders
            FROM transactions t
            JOIN products p
                ON t.product_id = p.product_id
            GROUP BY p.category
            ORDER BY revenue DESC;
        """)).fetchall()

        store_data = conn.execute(text("""
            SELECT
                s.store_name,
                SUM(t.total_amount) AS revenue
            FROM transactions t
            JOIN stores s
                ON t.store_id = s.store_id
            GROUP BY s.store_name
            ORDER BY revenue DESC
            LIMIT 10;
        """)).fetchall()

        daily_data = conn.execute(text("""
            SELECT
                DATE(transaction_date) AS sale_date,
                SUM(total_amount) AS revenue
            FROM transactions
            GROUP BY DATE(transaction_date)
            ORDER BY sale_date;
        """)).fetchall()

    categories = [row[0] for row in category_data]
    category_revenue = [float(row[1]) for row in category_data]

    stores = [row[0] for row in store_data]
    store_revenue = [float(row[1]) for row in store_data]

    dates = [row[0] for row in daily_data]
    daily_revenue = [float(row[1]) for row in daily_data]

    category_chart = px.bar(
        x=categories,
        y=category_revenue,
        title="Revenue by Category",
        color=category_revenue,
        color_continuous_scale="Blues"
    )

    category_chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font_color="white",
        coloraxis_showscale=False
    )

    store_chart = px.bar(
        x=stores,
        y=store_revenue,
        title="Top 10 Stores by Revenue",
        color=store_revenue,
        color_continuous_scale="Blues"
    )

    store_chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font_color="white",
        coloraxis_showscale=False
    )

    daily_chart = px.line(
        x=dates,
        y=daily_revenue,
        title="Daily Revenue Trend"
    )

    daily_chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font_color="white"
    )

    return render_template(
        "analytics.html",
        category_chart=category_chart.to_html(full_html=False),
        store_chart=store_chart.to_html(full_html=False),
        daily_chart=daily_chart.to_html(full_html=False)
    )


# ============================================================
# PRODUCTS
# ============================================================

@app.route("/products")
def products():

    with engine.connect() as conn:

        product_data = conn.execute(text("""
            SELECT
                p.product_id,
                p.product_name,
                p.category,
                p.price,
                p.stock_quantity,
                COALESCE(SUM(t.quantity), 0) AS units_sold,
                COALESCE(SUM(t.total_amount), 0) AS revenue
            FROM products p
            LEFT JOIN transactions t
                ON p.product_id = t.product_id
            GROUP BY
                p.product_id,
                p.product_name,
                p.category,
                p.price,
                p.stock_quantity
            ORDER BY revenue DESC
            LIMIT 50;
        """)).fetchall()

    return render_template(
        "products.html",
        products=product_data
    )


# ============================================================
# CUSTOMERS
# ============================================================

@app.route("/customers")
def customers():

    with engine.connect() as conn:

        customer_data = conn.execute(text("""
            SELECT
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                c.city,
                COUNT(t.transaction_id) AS orders,
                COALESCE(SUM(t.total_amount), 0) AS spending
            FROM customers c
            LEFT JOIN transactions t
                ON c.customer_id = t.customer_id
            GROUP BY
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                c.city
            ORDER BY spending DESC
            LIMIT 50;
        """)).fetchall()

    return render_template(
        "customers.html",
        customers=customer_data
    )


# ============================================================
# STORES
# ============================================================

@app.route("/stores")
def stores():

    with engine.connect() as conn:

        store_data = conn.execute(text("""
            SELECT
                s.store_id,
                s.store_name,
                s.city,
                COUNT(t.transaction_id) AS orders,
                COALESCE(SUM(t.total_amount), 0) AS revenue,
                COALESCE(AVG(t.total_amount), 0) AS average_sale
            FROM stores s
            LEFT JOIN transactions t
                ON s.store_id = t.store_id
            GROUP BY
                s.store_id,
                s.store_name,
                s.city
            ORDER BY revenue DESC;
        """)).fetchall()

    return render_template(
        "stores.html",
        stores=store_data
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
def reports():

    with engine.connect() as conn:

        total_revenue = conn.execute(
            text("SELECT COALESCE(SUM(total_amount), 0) FROM transactions")
        ).scalar()

        total_orders = conn.execute(
            text("SELECT COUNT(*) FROM transactions")
        ).scalar()

        average_sale = conn.execute(
            text("SELECT COALESCE(AVG(total_amount), 0) FROM transactions")
        ).scalar()

        top_category = conn.execute(text("""
            SELECT
                p.category
            FROM transactions t
            JOIN products p
                ON t.product_id = p.product_id
            GROUP BY p.category
            ORDER BY SUM(t.total_amount) DESC
            LIMIT 1;
        """)).scalar()

        top_store = conn.execute(text("""
            SELECT
                s.store_name
            FROM transactions t
            JOIN stores s
                ON t.store_id = s.store_id
            GROUP BY s.store_name
            ORDER BY SUM(t.total_amount) DESC
            LIMIT 1;
        """)).scalar()

    return render_template(
        "reports.html",
        total_revenue=float(total_revenue),
        total_orders=total_orders,
        average_sale=float(average_sale),
        top_category=top_category,
        top_store=top_store
    )




if __name__ == "__main__":
    app.run(debug=True)