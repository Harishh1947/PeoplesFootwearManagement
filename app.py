from flask import Flask, render_template, request, redirect, session
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime


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
    "b4": {"password": "123", "role": "manager", "branch_id": 4},
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

    # 🔒 auth check
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

    # =========================
    # POST
    # =========================
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
            session["msg"] = "❌ Entry already exists!"
            return redirect("/manager")

        # values
        sale = to_float(data.get("sale"))
        manual_sale = to_float(data.get("manual_sale"))
        expenses = to_float(data.get("expenses"))
        stationary = to_float(data.get("stationary"))
        phonepay = to_float(data.get("phonepay"))
        credit = to_float(data.get("credit"))
        freight = to_float(data.get("freight"))
        discount = to_float(data.get("discount"))
        bank = to_float(data.get("bank"))
        cpp = to_float(data.get("cpp"))
        company = to_float(data.get("company_payments"))
        taxes = to_float(data.get("taxes_expenses"))
        chappals = to_float(data.get("chappals_repair"))
        packing = to_float(data.get("packing_material"))
        furniture = to_float(data.get("furniture_repair"))
        net_bills = to_float(data.get("net_bills"))
        publicity = to_float(data.get("publicity_expenses"))
        travel = to_float(data.get("travel_allowance"))
        anniversary = to_float(data.get("anniversary_expenses"))

        rent = to_float(data.get("rent"))
        electricity = to_float(data.get("electricity"))
        sweeper_salary = to_float(data.get("sweeper_salary"))

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


        # 🆕 salesman advances
        advance_ids = request.form.getlist("advance_salesman_id")
        advance_types = request.form.getlist("advance_type")
        advance_amounts = request.form.getlist("advance_amount")

        advance_credit_total = 0
        advance_debit_total = 0

        for typ, amt in zip(advance_types, advance_amounts):

            value = to_float(amt)

            if typ == "credit":
                advance_credit_total += value
            else:
                advance_debit_total += value
        # date split
        month = int(date.split("-")[1])
        year = int(date.split("-")[0])

        # closing
        closing = (
            opening + sale + manual_sale + advance_credit_total 
            - phonepay - credit - expenses - stationary
            - discount
            - freight - bank - cpp
            - rent - electricity
            - salary_total
            - sweeper_salary
            - commission_total
            - sales_comm_total
            - company - taxes - chappals
            - packing - furniture - net_bills
            - advance_debit_total - publicity - travel - anniversary
        )

        # 🔹 daily entry
        entry = supabase.table("daily_entry").insert({
            "branch_id": branch_id,
            "entry_date": date,
            "opening_balance": opening,
            "daily_sale": sale,
            "manual_sale": manual_sale,
            "daily_expenses": expenses,
            "discount": discount,
            "stationary_expenses": stationary,
            "phonepay": phonepay,
            "credit_card": credit,
            "freight_charges": freight,
            "bank_deposit": bank,
            "cpp_account": cpp,
            "rent": rent,
            "electricity_bill": electricity,
            "salaries": salary_total,
            "sweeper_salary": sweeper_salary,
            "commission_total": commission_total,
            "company_payments": company,
            "taxes_expenses": taxes,
            "chappals_repair": chappals,
            "packing_material": packing,
            "furniture_repair": furniture,
            "net_bills": net_bills,
            "publicity_expenses": publicity,
            "travel_allowance": travel,
            "anniversary_expenses": anniversary,
            "closing_balance": closing
        }).execute()

        entry_id = entry.data[0]["id"]

        # 🔹 salary insert
        for sid, amt in zip(salary_ids, salary_amounts):
            if amt:
                supabase.table("salesman_salary").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "month": month,
                    "year": year,
                    "salary": float(amt),
                    "daily_entry_id": entry_id
                }).execute()

        # 🔹 special commission
        for sid, amt in zip(ids, amts):
            if amt:
                supabase.table("special_commission").insert({
                    "daily_entry_id": entry_id,
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "amount": float(amt)
                }).execute()

        # 🔹 sales commission
        from datetime import datetime
        for sid, amt in zip(sales_comm_ids, sales_comm_amounts):
            if amt:
                supabase.table("salesman_sales_commission").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "entry_datetime": datetime.now().isoformat(),
                    "amount": float(amt),
                    "daily_entry_id": entry_id
                }).execute()

        # 🔹 salesman advances
        for sid, typ, amt in zip(advance_ids, advance_types, advance_amounts):

            if amt:

                supabase.table("salesman_advance_entry").insert({
                    "salesman_id": int(sid),
                    "branch_id": branch_id,
                    "advance_mode": typ,
                    "amount": float(amt),
                    "daily_entry_id": entry_id
                }).execute()

        # ✅ success message + redirect
        session["msg"] = "✅ Saved Successfully!"
        return redirect("/manager")

    # =========================
    # GET
    # =========================
    return render_template(
        "manager.html",
        opening=opening,
        branch_salesmen=branch_salesmen,
        overall_balance=0,
        advance_report=[],
        other_salesmen=other_salesmen
    )


# 📊 Admin
@app.route("/admin", methods=["GET", "POST"])
def admin():

    # 🔒 Security
    if "user" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "❌ Unauthorized"

    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")
    branch_id = request.form.get("branch_id")
    report_type = request.form.get("report_type")

    daily_ids = []

    if from_date and to_date:

        daily_query = supabase.table("daily_entry")\
            .select("id")

        daily_query = daily_query.gte("entry_date", from_date)\
                                .lte("entry_date", to_date)

        if branch_id not in [None, "", "None", "all"]:
            daily_query = daily_query.eq("branch_id", int(branch_id))

        daily_data = daily_query.execute().data

        daily_ids = [x["id"] for x in daily_data]

    action = request.form.get("action")

    advance_salesman_id = request.form.get("advance_salesman_id")

    advance_from_date = request.form.get("advance_from_date")

    advance_to_date = request.form.get("advance_to_date")

    # Branches
    branches = supabase.table("branch").select("id,name").execute().data
    salesmen = supabase.table("salesman")\
        .select("id,name")\
        .execute().data


    # 💰 Cash
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

    advance_report = []
    overall_balance = 0

    # =========================
    # DEFAULT LOAD
    # =========================
    if request.method == "GET":
        return render_template(
            "admin.html",
            report_type=None,
            branches=branches,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            from_date=from_date,
            to_date=to_date,
            selected_branch=branch_id,
            salesmen=salesmen,
            overall_balance=0,
            advance_report=[]
        )

    # =========================
    # 💵 ADVANCES
    # =========================

    if action == "advance_report":

        # 🔹 get daily ids from selected range
        advance_daily_ids = []

        daily_query = supabase.table("daily_entry")\
            .select("id, entry_date")
        
        if branch_id not in [None, "", "None", "all"]:
            daily_query = daily_query.eq("branch_id", int(branch_id))

        if advance_from_date and advance_to_date:

            daily_query = daily_query.gte(
                "entry_date",
                advance_from_date
            ).lte(
                "entry_date",
                advance_to_date
            )

        daily_data = daily_query.execute().data

        advance_daily_ids = [x["id"] for x in daily_data]
        print("ADVANCE IDS:", advance_daily_ids)

        # 🔹 selected period query
        query = supabase.table("salesman_advance_entry")\
            .select("*")\
            .eq("salesman_id", int(advance_salesman_id))

        if advance_daily_ids:
            query = query.in_("daily_entry_id", advance_daily_ids)
        else:
            query = query.eq("daily_entry_id", -1)

        data = query.execute().data

        # 🔹 report rows
        for row in data:

            daily_res = supabase.table("daily_entry")\
                .select("entry_date")\
                .eq("id", row["daily_entry_id"])\
                .execute()

            entry_date = ""

            if daily_res.data:
                entry_date = daily_res.data[0]["entry_date"]

            advance_report.append({
                "date": entry_date,
                "type": row["advance_mode"],
                "amount": row["amount"]
            })

        # 🔥 OVERALL BALANCE (ALL TIME)
        overall_query = supabase.table("salesman_advance_entry")\
            .select("advance_mode, amount")\
            .eq("salesman_id", int(advance_salesman_id))\
            .execute()

        for row in overall_query.data:

            if row["advance_mode"] == "debit":
                overall_balance -= row["amount"]

            else:
                overall_balance += row["amount"]

        return render_template(
            "admin.html",
            branches=branches,
            salesmen=salesmen,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            advance_report=advance_report,
            overall_balance=overall_balance,
            selected_salesman=advance_salesman_id,
            advance_from_date=advance_from_date,
            advance_to_date=advance_to_date,
            from_date=from_date,
            to_date=to_date,
            selected_branch=branch_id,
            report_type=None
        )

    # =========================
    # SUMMARY / MONTHLY
    # =========================
    if report_type in ["summary", "monthly"]:

        query = supabase.table("daily_entry").select("*")

        if from_date and to_date:
            query = query.gte("entry_date", from_date)\
                        .lte("entry_date", to_date)

        if branch_id not in [None, "", "None", "all"]:
            query = query.eq("branch_id", int(branch_id))

        data = query.execute().data

        total_sales = total_expenses = total_stationary = 0
        total_manual_sale = 0
        base_salary_total = 0
        total_phonepay = total_credit = total_freight = 0
        total_bank = total_cpp = total_discount = 0
        total_rent = total_electricity = total_salary = total_sweeper_salary = 0
        total_commission = 0
        total_company = total_taxes = total_chappals = 0
        total_packing = total_furniture = total_net_bills = 0
        total_publicity = total_travel = total_anniversary = 0

        monthly_rent = monthly_electricity = monthly_salary = monthly_sweeper_salary = monthly_net_bills = 0

        # ✅ FIX 1: move outside loop
        sales_comm_total = 0

        # ✅ FIX 2: safe date usage
        if from_date and to_date:
            sales_query = supabase.table("salesman_sales_commission")\
                .select("amount")

            if daily_ids:
                sales_query = sales_query.in_("daily_entry_id", daily_ids)

            sales_data = sales_query.execute().data
            
        else:
            sales_data = supabase.table("salesman_sales_commission")\
                .select("amount")\
                .execute().data

        for row in sales_data:
            sales_comm_total += row.get("amount", 0)
        # 🔹 Special Commission total
        special_total = 0
        
        special_query = supabase.table("special_commission")\
            .select("amount")
        
        
        if branch_id not in [None, "", "None", "all"]:
            special_query = special_query.eq("branch_id", int(branch_id))
        
        special_data = special_query.execute().data
        
        for row in special_data:
            special_total += row.get("amount", 0)



        for r in data:
            total_sales += r.get("daily_sale", 0)
            total_manual_sale += r.get("manual_sale", 0)
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
            base_salary_total += r.get("salaries", 0)
            total_sweeper_salary += r.get("sweeper_salary", 0)
            monthly_sweeper_salary += r.get("sweeper_salary", 0)
            total_commission += r.get("commission_total", 0)

            total_company += r.get("company_payments", 0)
            total_taxes += r.get("taxes_expenses", 0)
            total_chappals += r.get("chappals_repair", 0)
            total_packing += r.get("packing_material", 0)
            total_furniture += r.get("furniture_repair", 0)
            total_net_bills += r.get("net_bills", 0)
            total_publicity += r.get("publicity_expenses", 0)
            total_travel += r.get("travel_allowance", 0)
            total_anniversary += r.get("anniversary_expenses", 0)

            monthly_rent += r.get("rent", 0)
            monthly_electricity += r.get("electricity_bill", 0)
            monthly_salary += r.get("salaries", 0)
            monthly_net_bills += r.get("net_bills", 0)


        # ✅ FINAL SALARY FIX
        total_salary = (
            total_salary
            + special_total
            + sales_comm_total
        )


        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            total_sales=total_sales,
            total_manual_sale=total_manual_sale,
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
            base_salary_total=base_salary_total,
            special_total=special_total,
            sales_comm_total=sales_comm_total,
            
            
            total_commission=total_commission,
            total_company=total_company,
            total_taxes=total_taxes,
            total_chappals=total_chappals,
            total_packing=total_packing,
            total_furniture=total_furniture,
            total_net_bills=total_net_bills,
            total_publicity=total_publicity,
            total_travel=total_travel,
            total_anniversary=total_anniversary,
            monthly_rent=monthly_rent,
            monthly_electricity=monthly_electricity,
            monthly_salary=monthly_salary,
            monthly_net_bills=monthly_net_bills,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            
            from_date=from_date,
            to_date=to_date,
            selected_branch=branch_id,
            salesmen=salesmen,
            total_sweeper_salary=total_sweeper_salary,
            monthly_sweeper_salary=monthly_sweeper_salary,
            advance_report=advance_report,
            overall_balance=overall_balance,
            selected_salesman=advance_salesman_id,
            advance_from_date=advance_from_date,
            advance_to_date=advance_to_date

        )

    # =========================
    # SALES COMMISSION
    # =========================
    elif report_type == "sales_commission":
    
        query = supabase.table("salesman_sales_commission")\
            .select("amount, salesman_id")
    
        # ✅ FIX 1: safe date filter
        if daily_ids:
            query = query.in_("daily_entry_id", daily_ids)
    
        # ✅ FIX 2: branch filter
        if branch_id not in [None, "", "None", "all"]:
            query = query.eq("branch_id", int(branch_id))
    
        sales_comm_data = query.execute().data
    
        sales_comm_report = {}
    
        for row in sales_comm_data:
            sid = row["salesman_id"]
    
            res = supabase.table("salesman")\
                .select("name, branch_id")\
                .eq("id", sid)\
                .execute()
    
            name = res.data[0]["name"] if res.data else "Unknown"
    
            sales_comm_report[name] = sales_comm_report.get(name, 0) + row["amount"]
    
        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            sales_comm_report=sales_comm_report,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            from_date=from_date,
            to_date=to_date,
            selected_branch=branch_id,
            overall_balance=0,
            salesmen=salesmen,
            advance_report=[]
        )
    elif report_type == "commission":

        query = supabase.table("special_commission")\
            .select("amount, salesman_id")
    
        # ✅ Date filter
        # ✅ filter only by date
        if from_date and to_date:

            daily_res = supabase.table("daily_entry")\
                .select("id")\
                .gte("entry_date", from_date)\
                .lte("entry_date", to_date)\
                .execute()

            all_date_daily_ids = [x["id"] for x in daily_res.data]

            if all_date_daily_ids:
                query = query.in_("daily_entry_id", all_date_daily_ids)
    
        
    
        data = query.execute().data
    
        commission_report = {}
    
        for row in data:
            sid = row["salesman_id"]
    
            res = supabase.table("salesman")\
                .select("name, branch_id")\
                .eq("id", sid)\
                .execute()

            if not res.data:
                continue

            salesman = res.data[0]
            # ✅ filter using salesman assigned branch
            if branch_id not in [None, "", "None", "all"]:

                if int(salesman["branch_id"]) != int(branch_id):
                    continue


            name = salesman["name"]

            commission_report[name] = (
                commission_report.get(name, 0)
                + row["amount"]
            )
    
        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            commission_report=commission_report,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            from_date=from_date,
            to_date=to_date,
            salesmen=salesmen,
            selected_branch=branch_id,
            overall_balance=0,
            advance_report=[]
        )

    
    elif report_type == "salary":

        salary_map = {}
        special_map = {}
        sales_map = {}
    
        # 🔹 Salary (WITH branch + date filter)
        salary_query = supabase.table("salesman_salary")\
            .select("salary, salesman_id")
    
        if branch_id not in [None, "", "None", "all"]:
            salary_query = salary_query.eq("branch_id", int(branch_id))
    
        # ✅ filter only by date
        if from_date and to_date:

            daily_res = supabase.table("daily_entry")\
                .select("id")\
                .gte("entry_date", from_date)\
                .lte("entry_date", to_date)\
                .execute()

            all_date_daily_ids = [x["id"] for x in daily_res.data]

    
        salary_data = salary_query.execute().data
    
        for row in salary_data:
            sid = row["salesman_id"]
    
            res = supabase.table("salesman")\
                .select("name, branch_id")\
                .eq("id", sid)\
                .execute()
    
            name = res.data[0]["name"] if res.data else "Unknown"
    
            salary_map[name] = salary_map.get(name, 0) + row["salary"]
    
        # 🔹 Special Commission
        special_query = supabase.table("special_commission")\
            .select("amount, salesman_id")

        # ✅ filter only by date
        if from_date and to_date:

            daily_res = supabase.table("daily_entry")\
                .select("id")\
                .gte("entry_date", from_date)\
                .lte("entry_date", to_date)\
                .execute()

            all_date_daily_ids = [x["id"] for x in daily_res.data]



        special_data = special_query.execute().data

        for row in special_data:
            sid = row["salesman_id"]

            res = supabase.table("salesman")\
                .select("name, branch_id")\
                .eq("id", sid)\
                .execute()

            if not res.data:
                continue

            salesman = res.data[0]

            # ✅ filter by salesman own branch
            if branch_id not in [None, "", "None", "all"]:

                if salesman["branch_id"] != int(branch_id):
                    continue

            name = salesman["name"]

            special_map[name] = (
                special_map.get(name, 0)
                + row["amount"]
            )
    
        # 🔹 Sales Commission (WITH branch + date filter)
        sales_query = supabase.table("salesman_sales_commission")\
            .select("amount, salesman_id")
    
        if branch_id not in [None, "", "None", "all"]:
            sales_query = sales_query.eq("branch_id", int(branch_id))
    
        if daily_ids:
            sales_query = sales_query.in_("daily_entry_id", daily_ids)
    
        sales_data = sales_query.execute().data
    
        for row in sales_data:
            sid = row["salesman_id"]
    
            res = supabase.table("salesman")\
                .select("name, branch_id")\
                .eq("id", sid)\
                .execute()
    
            name = res.data[0]["name"] if res.data else "Unknown"
    
            sales_map[name] = sales_map.get(name, 0) + row["amount"]
    
        # 🔹 Combine
        final_salary_report = {}
    
        all_names = set(list(salary_map.keys()) +
                        list(special_map.keys()) +
                        list(sales_map.keys()))
    
        for name in all_names:
            sal = salary_map.get(name, 0)
            sp = special_map.get(name, 0)
            sc = sales_map.get(name, 0)
    
            total = sal + sp + sc
    
            final_salary_report[name] = {
                "salary": sal,
                "commission": sp,
                "sales_commission": sc,
                "total": total
            }
    
        return render_template(
            "admin.html",
            report_type=report_type,
            branches=branches,
            salary_report=final_salary_report,
            branch_cash_list=branch_cash_list,
            total_cash=total_cash,
            from_date=from_date,
            to_date=to_date,
            salesmen=salesmen,
            selected_branch=branch_id,
            overall_balance=0,
            advance_report=[]
        )
    




    
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
