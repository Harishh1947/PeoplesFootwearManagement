from flask import Flask, render_template, request, redirect, session
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# 🔐 Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise Exception("Missing Supabase credentials")

supabase = create_client(url, key)

# 🔧 Flask
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# 🔐 Users
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "b1": {"password": "123", "role": "manager", "branch_id": 1},
    "b2": {"password": "123", "role": "manager", "branch_id": 2},
    "b3": {"password": "123", "role": "manager", "branch_id": 3},
}

# 🧠 Utils
def to_float(val):
    return float(val) if val and val.strip() else 0


def get_opening(branch_id):
    res = supabase.table("daily_entry")\
        .select("closing_balance")\
        .eq("branch_id", branch_id)\
        .order("id", desc=True)\
        .limit(1)\
        .execute()

    if res.data:
        return res.data[0]["closing_balance"]
    else:
        res = supabase.table("branch")\
            .select("initial_opening_balance")\
            .eq("id", branch_id)\
            .execute()

        return res.data[0]["initial_opening_balance"]


# 🔐 Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u]["password"] == p:
            session["user"] = u
            session["role"] = users[u]["role"]

            if users[u]["role"] == "admin":
                return redirect("/admin")
            else:
                session["branch_id"] = users[u]["branch_id"]
                return redirect("/manager")

    return render_template("login.html")


# 🔓 Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 📝 Manager
@app.route("/manager", methods=["GET", "POST"])
def manager():

    if "user" not in session:
        return redirect("/")

    if session.get("role") != "manager":
        return "❌ Unauthorized"

    branch_id = session.get("branch_id")
    opening = get_opening(branch_id)

    branch_salesmen = supabase.table("salesman")\
        .select("id,name")\
        .eq("branch_id", branch_id)\
        .execute().data

    other_salesmen = supabase.table("salesman")\
        .select("id,name")\
        .neq("branch_id", branch_id)\
        .execute().data

    if request.method == "POST":

        data = request.form
        date = data.get("date")

        # ❗ duplicate check
        existing = supabase.table("daily_entry")\
            .select("id")\
            .eq("branch_id", branch_id)\
            .eq("entry_date", date)\
            .execute()

        if existing.data:
            return "❌ Entry already exists!"

        # values
        sale = to_float(data.get("sale"))
        expenses = to_float(data.get("expenses"))
        stationary = to_float(data.get("stationary"))
        phonepay = to_float(data.get("phonepay"))
        credit = to_float(data.get("credit"))
        freight = to_float(data.get("freight"))
        bank = to_float(data.get("bank"))
        cpp = to_float(data.get("cpp"))
        company = to_float(data.get("company_payments"))
        taxes = to_float(data.get("taxes_expenses"))
        chappals = to_float(data.get("chappals_repair"))
        packing = to_float(data.get("packing_material"))
        furniture = to_float(data.get("furniture_repair"))
        net_bills = to_float(data.get("net_bills"))
        adv_debit = to_float(data.get("advance_debit"))
        adv_credit = to_float(data.get("advance_credit"))
        publicity = to_float(data.get("publicity_expenses"))
        travel = to_float(data.get("travel_allowance"))
        anniversary = to_float(data.get("anniversary_expenses"))

        rent = to_float(data.get("rent"))
        electricity = to_float(data.get("electricity"))

        # salary
        salary_ids = request.form.getlist("salary_salesman_id")
        salary_amounts = request.form.getlist("salary_amount")

        salary_total = sum([to_float(x) for x in salary_amounts])

        # special commission
        ids = request.form.getlist("salesman_id")
        amts = request.form.getlist("amount")

        commission_total = sum([to_float(x) for x in amts])

        # 🆕 sales commission
        sales_comm_ids = request.form.getlist("sales_comm_salesman_id")
        sales_comm_amounts = request.form.getlist("sales_comm_amount")

        sales_comm_total = sum([to_float(x) for x in sales_comm_amounts])

        # date split
        month = int(date.split("-")[1])
        year = int(date.split("-")[0])

        # closing balance
        closing = (
            opening + sale + adv_credit
            - phonepay - credit - expenses - stationary
            - freight - bank - cpp
            - rent - electricity
            - salary_total
            - commission_total
            - sales_comm_total
            - company - taxes - chappals
            - packing - furniture - net_bills
            - adv_debit - publicity - travel - anniversary
        )

        entry = supabase.table("daily_entry").insert({
            "branch_id": branch_id,
            "entry_date": date,
            "opening_balance": opening,
            "daily_sale": sale,
            "daily_expenses": expenses,
            "stationary_expenses": stationary,
            "phonepay": phonepay,
            "credit_card": credit,
            "freight_charges": freight,
            "bank_deposit": bank,
            "cpp_account": cpp,
            "rent": rent,
            "electricity_bill": electricity,
            "salaries": salary_total,
            "commission_total": commission_total,
            "company_payments": company,
            "taxes_expenses": taxes,
            "chappals_repair": chappals,
            "packing_material": packing,
            "furniture_repair": furniture,
            "net_bills": net_bills,
            "advance_debit": adv_debit,
            "advance_credit": adv_credit,
            "publicity_expenses": publicity,
            "travel_allowance": travel,
            "anniversary_expenses": anniversary,
            "closing_balance": closing
        }).execute()

        entry_id = entry.data[0]["id"]

        # salary insert
        for sid, amt in zip(salary_ids, salary_amounts):
            if amt:
                supabase.table("salesman_salary").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "month": month,
                    "year": year,
                    "salary": float(amt)
                }).execute()

        # special commission insert
        for sid, amt in zip(ids, amts):
            if amt:
                supabase.table("special_commission").insert({
                    "daily_entry_id": entry_id,
                    "salesman_id": int(sid),
                    "amount": float(amt)
                }).execute()

        # 🆕 sales commission insert
        for sid, amt in zip(sales_comm_ids, sales_comm_amounts):
            if amt:
                supabase.table("salesman_sales_commission").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "month": month,
                    "year": year,
                    "amount": float(amt)
                }).execute()

        return "✅ Saved Successfully!"

    return render_template(
        "manager.html",
        opening=opening,
        branch_salesmen=branch_salesmen,
        other_salesmen=other_salesmen
    )


# 📊 Admin
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "user" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "❌ Unauthorized"

    branches = supabase.table("branch").select("id,name").execute().data

    # 💰 cash
    branch_cash_list = []
    total_cash = 0

    for b in branches:
        res = supabase.table("daily_entry")\
            .select("closing_balance")\
            .eq("branch_id", b["id"])\
            .order("id", desc=True)\
            .limit(1)\
            .execute()

        cash = res.data[0]["closing_balance"] if res.data else 0
        total_cash += cash

        branch_cash_list.append({
            "name": b["name"],
            "cash": cash
        })

    # 🆕 sales commission report (always available)
    sales_comm_data = supabase.table("salesman_sales_commission")\
        .select("amount, salesman(name)")\
        .execute().data

    sales_comm_report = {}
    for row in sales_comm_data:
        name = row["salesman"]["name"]
        sales_comm_report[name] = sales_comm_report.get(name, 0) + row["amount"]

    return render_template(
        "admin.html",
        branches=branches,
        branch_cash_list=branch_cash_list,
        total_cash=total_cash,
        sales_comm_report=sales_comm_report
    )


# 🚀 Run
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
