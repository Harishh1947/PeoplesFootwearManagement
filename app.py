from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)
if not url or not key:
    raise Exception("Missing Supabase credentials")

app = Flask(__name__)
app.secret_key = "change_this_to_random_secret_123"
# 🔐 Users
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "b1": {"password": "123", "role": "manager", "branch_id": 1},
    "b2": {"password": "123", "role": "manager", "branch_id": 2},
    "b3": {"password": "123", "role": "manager", "branch_id": 3},
}

# 🧠 Safe float
def to_float(val):
    return float(val) if val and val.strip() else 0

# 🧠 Opening balance
def get_opening(branch_id):
    res = supabase.table("daily_entry")\
        .select("closing_balance")\
        .eq("branch_id", branch_id)\
        .order("id", desc=True)\
        .limit(1)\
        .execute()

    if res.data and len(res.data) > 0:
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

            # ✅ store session
            session["user"] = u
            session["role"] = users[u]["role"]

            if users[u]["role"] == "admin":
                return redirect("/admin")
            else:
                session["branch_id"] = users[u]["branch_id"]
                return redirect("/manager")

    return render_template("login.html")


# 📝 Manager
@app.route("/manager", methods=["GET", "POST"])
def manager():

    # 🔒 login check
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

    # keep your existing POST logic SAME (no change)

    return render_template(
        "manager.html",
        opening=opening,
        branch_salesmen=branch_salesmen,
        other_salesmen=other_salesmen
    )

    if request.method == "POST":
        data = request.form
        date = data.get("date")

        # ❗ Prevent duplicate entry
        existing = supabase.table("daily_entry")\
            .select("id")\
            .eq("branch_id", branch_id)\
            .eq("entry_date", date)\
            .execute()

        if existing.data:
            return "❌ Entry already exists for this date!"

        # values
        sale = to_float(data.get("sale"))
        expenses = to_float(data.get("expenses"))
        stationary = to_float(data.get("stationary"))
        phonepay = to_float(data.get("phonepay"))
        credit = to_float(data.get("credit"))
        freight = to_float(data.get("freight"))
        bank = to_float(data.get("bank"))
        discount = to_float(data.get("discount"))
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

        # ❗ Only allow discount for branch 1
        if branch_id == 1:
            discount = to_float(data.get("discount"))
        else:
            discount = 0

        rent = to_float(data.get("rent"))
        electricity = to_float(data.get("electricity"))
        salary_total = 0

        salary_ids = request.form.getlist("salary_salesman_id")
        salary_amounts = request.form.getlist("salary_amount")

        for amt in salary_amounts:
            if amt and amt.strip():
                salary_total += float(amt)
        # 🆕 SALES COMMISSION (MONTHLY)
        sales_comm_ids = request.form.getlist("sales_comm_salesman_id")
        sales_comm_amounts = request.form.getlist("sales_comm_amount")
        
        sales_comm_total = 0
        
        for amt in sales_comm_amounts:
            if amt and amt.strip():
                sales_comm_total += float(amt)

        commission_total = 0

        salesman_ids = request.form.getlist("salesman_id")
        amounts = request.form.getlist("amount")

        for amt in amounts:
            if amt and amt.strip():
                commission_total += float(amt)

        closing = (
            opening
            + sale
            + adv_credit
            - phonepay
            - credit
            - expenses
            - stationary
            - freight
            - bank
            - cpp
            - discount
            - rent
            - electricity
            - salary_total
            - sales_comm_total
            - commission_total
            - company
            - taxes
            - chappals
            - packing
            - furniture
            - net_bills
            - adv_debit
            - publicity
            - travel
            - anniversary
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
            "discount": discount,
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
        # 💰 Salary Insert (Monthly)
        salary_ids = request.form.getlist("salary_salesman_id")
        salary_amounts = request.form.getlist("salary_amount")
        # 🆕 Insert Sales Commission
        for sid, amt in zip(sales_comm_ids, sales_comm_amounts):
            if amt and amt.strip():
                supabase.table("salesman_sales_commission").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "month": month,
                    "year": year,
                    "amount": float(amt)
                }).execute()

        month = int(date.split("-")[1])
        year = int(date.split("-")[0])

        for sid, amt in zip(salary_ids, salary_amounts):
            if amt and amt.strip():
                supabase.table("salesman_salary").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "month": month,
                    "year": year,
                    "salary": float(amt)
                }).execute()
        
        

        # commission
        ids = request.form.getlist("salesman_id")
        amts = request.form.getlist("amount")

        for sid, amt in zip(ids, amts):
            if amt and amt.strip():
                supabase.table("special_commission").insert({
                    "daily_entry_id": entry_id,
                    "salesman_id": int(sid),
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
    sales_comm_report = {}
    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")
    branch_id = request.form.get("branch_id")
    report_type = request.form.get("report_type")

    # get branches
    branches = supabase.table("branch").select("id,name").execute().data
    # 💰 Available Cash (always visible)
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

        branch_cash_list.append({
            "name": b["name"],
            "cash": cash
        })

        total_cash += cash
    if request.method == "GET":
        return render_template(
            "admin.html",
            report_type=None,
            branches=branches,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash
        )
    
    
    

    # -----------------------------
    # 📊 SUMMARY / MONTHLY REPORT
    # -----------------------------
    if report_type in ["summary", "monthly"]:

        query = supabase.table("daily_entry").select("*")

        if from_date and to_date:
            query = query.gte("entry_date", from_date).lte("entry_date", to_date)

        if branch_id and branch_id != "all":
            query = query.eq("branch_id", int(branch_id))

        data = query.execute().data

        # totals
        total_sales = total_expenses = total_stationary = 0
        total_phonepay = total_credit = total_freight = 0
        total_bank = total_cpp = total_discount = 0
        total_rent = total_electricity = total_salary = 0
        total_commission = 0

        total_company = total_taxes = total_chappals = 0
        total_packing = total_furniture = total_net_bills = 0
        total_adv_debit = total_adv_credit = 0
        total_publicity = total_travel = total_anniversary = 0

        # monthly
        monthly_rent = monthly_electricity = monthly_salary = monthly_net_bills = 0

        for r in data:
            total_sales += r.get("daily_sale", 0)
            total_expenses += r.get("daily_expenses", 0)
            total_stationary += r.get("stationary_expenses", 0)
            total_phonepay += r.get("phonepay", 0)
            total_credit += r.get("credit_card", 0)
            total_freight += r.get("freight_charges", 0)
            total_bank += r.get("bank_deposit", 0)
            total_cpp += r.get("cpp_account", 0)
            total_discount += r.get("discount", 0)
            total_rent += r.get("rent", 0)
            total_electricity += r.get("electricity_bill", 0)
            total_salary += r.get("salaries", 0)
            total_commission += r.get("commission_total", 0)

            total_company += r.get("company_payments", 0)
            total_taxes += r.get("taxes_expenses", 0)
            total_chappals += r.get("chappals_repair", 0)
            total_packing += r.get("packing_material", 0)
            total_furniture += r.get("furniture_repair", 0)
            total_net_bills += r.get("net_bills", 0)
            total_adv_debit += r.get("advance_debit", 0)
            total_adv_credit += r.get("advance_credit", 0)
            total_publicity += r.get("publicity_expenses", 0)
            total_travel += r.get("travel_allowance", 0)
            total_anniversary += r.get("anniversary_expenses", 0)

            monthly_rent += r.get("rent", 0)
            monthly_electricity += r.get("electricity_bill", 0)
            monthly_salary += r.get("salaries", 0)
            monthly_net_bills += r.get("net_bills", 0)

        
        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            total_sales=total_sales,
            total_expenses=total_expenses,
            total_stationary=total_stationary,
            total_phonepay=total_phonepay,
            total_credit=total_credit,
            total_freight=total_freight,
            total_bank=total_bank,
            total_cpp=total_cpp,
            total_discount=total_discount,
            total_rent=total_rent,
            total_electricity=total_electricity,
            total_salary=total_salary,
            total_commission=total_commission,
            total_company=total_company,
            total_taxes=total_taxes,
            total_chappals=total_chappals,
            total_packing=total_packing,
            total_furniture=total_furniture,
            total_net_bills=total_net_bills,
            total_adv_debit=total_adv_debit,
            total_adv_credit=total_adv_credit,
            total_publicity=total_publicity,
            total_travel=total_travel,
            total_anniversary=total_anniversary,
            monthly_rent=monthly_rent,
            monthly_electricity=monthly_electricity,
            monthly_salary=monthly_salary,
            monthly_net_bills=monthly_net_bills,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
        )

    # -----------------------------
    # 💰 COMMISSION REPORT
    # -----------------------------
    elif report_type == "commission":

        query = supabase.table("special_commission")\
            .select("amount, salesman!special_commission_salesman_id_fkey(name), daily_entry(entry_date)")

        if from_date and to_date:
            query = query.gte("daily_entry.entry_date", from_date)\
                         .lte("daily_entry.entry_date", to_date)

        commission_data = query.execute().data

        commission_report = {}

        for row in commission_data:
            name = row["salesman"]["name"]
            commission_report[name] = commission_report.get(name, 0) + row["amount"]

        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            commission_report=commission_report,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash
        )

    # -----------------------------
    # 🧾 SALARY REPORT
    # -----------------------------
    elif report_type == "salary":

        salary_map = {}
        commission_map = {}

        # ----------------------------
        # 🔹 Parse date range
        # ----------------------------
        if from_date and to_date:
            from_year, from_month = map(int, from_date.split("-")[:2])
            to_year, to_month = map(int, to_date.split("-")[:2])

            salary_query = supabase.table("salesman_salary")\
                .select("salary, salesman!salesman_salary_salesman_id_fkey(name), month, year")

            salary_data = salary_query.execute().data

            # filter manually (safe + flexible)
            filtered_salary = []

            for row in salary_data:
                y = row["year"]
                m = row["month"]

                if (y > from_year or (y == from_year and m >= from_month)) and \
                (y < to_year or (y == to_year and m <= to_month)):
                    filtered_salary.append(row)

        else:
            filtered_salary = []

        # ----------------------------
        # 🔹 Salary aggregation
        # ----------------------------
        for row in filtered_salary:
            name = row["salesman"]["name"]
            salary_map[name] = salary_map.get(name, 0) + row["salary"]

        # ----------------------------
        # 🔹 Commission (date based)
        # ----------------------------
        commission_query = supabase.table("special_commission")\
            .select("amount, salesman!special_commission_salesman_id_fkey(name), daily_entry(entry_date)")

        if from_date and to_date:
            commission_query = commission_query\
                .gte("daily_entry.entry_date", from_date)\
                .lte("daily_entry.entry_date", to_date)

        commission_data = commission_query.execute().data

        for row in commission_data:
            name = row["salesman"]["name"]
            commission_map[name] = commission_map.get(name, 0) + row["amount"]

        # ----------------------------
        # 🔹 Combine
        # ----------------------------
        final_salary_report = {}

        all_names = set(list(salary_map.keys()) + list(commission_map.keys()))

        for name in all_names:
            sal = salary_map.get(name, 0)
            com = commission_map.get(name, 0)

            final_salary_report[name] = {
                "salary": sal,
                "commission": com,
                "total": sal + com
            }
        sales_comm_data = supabase.table("salesman_sales_commission")\
            .select("amount, salesman(name)")\
            .execute().data
        
        sales_comm_report = {}
        
        for row in sales_comm_data:
            name = row["salesman"]["name"]
            sales_comm_report[name] = sales_comm_report.get(name, 0) + row["amount"]
        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            salary_report=final_salary_report,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            sales_comm_report=sales_comm_report
        )

        sales_comm_data = supabase.table("salesman_sales_commission")\
            .select("amount, salesman(name)")\
            .execute().data
        
        sales_comm_report = {}
        
        for row in sales_comm_data:
            name = row["salesman"]["name"]
            sales_comm_report[name] = sales_comm_report.get(name, 0) + row["amount"]
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
    
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
