from flask import make_response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from io import BytesIO
from email.mime import image
from openpyxl import Workbook
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, redirect,session,flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()
print("RUNNING FILE:", __file__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(BASE_DIR, "..", "templates")):
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
else:
    PROJECT_ROOT = BASE_DIR

app = Flask(
    
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static")
    
)
from jinja2 import FileSystemLoader

app.jinja_loader = FileSystemLoader(app.template_folder)

print(app.jinja_loader.searchpath)
print("Template Folder:", app.template_folder)
print("Static Folder:", app.static_folder)
print("Exists:", os.path.exists(app.template_folder))

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))
app.secret_key = "smartwaterguardian123"


print("HOST =", os.getenv("MYSQL_HOST"))
print("USER =", os.getenv("MYSQL_USER"))
print("DB =", os.getenv("MYSQL_DB"))
print("PORT =", os.getenv("MYSQL_PORT"))
print("PASSWORD =", os.getenv("MYSQL_PASSWORD"))

print("\n===== Flask Config =====")
print(app.config["MYSQL_HOST"])
print(app.config["MYSQL_USER"])
print(app.config["MYSQL_DB"])
print(app.config["MYSQL_PORT"])
print(app.config["MYSQL_PASSWORD"])
print("========================\n")

import MySQLdb

def get_db():
    return MySQLdb.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        port=int(os.getenv("MYSQL_PORT")),
        ssl_mode="REQUIRED",
        ssl={"ca": os.path.join(PROJECT_ROOT, "ca.pem")}
    )
print(">>> REGISTERING RAWTEST ROUTE <<<")

@app.route("/rawtest")
def rawtest():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT DATABASE()")
    print("Current DB:", cur.fetchone())

    cur.execute("SHOW TABLES")
    print("Tables:", cur.fetchall())

    cur.close()
    conn.close()

    return "OK"

@app.route("/")
def home():
    print("********HOME ROUT EXECUTED********")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM reports")
    total_reports = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'")
    pending_reports = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'")
    resolved_reports = cur.fetchone()[0]

    cur.close()
    conn.close()
    print("Rendering index.html")

    return render_template(
        "index.html",
        total_reports=total_reports,
        total_users=total_users,
        pending_reports=pending_reports,
        resolved_reports=resolved_reports
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SHOW COLUMNS FROM users")
        print("Columns:", cur.fetchall())

        cur.execute(
           "SELECT * FROM users WHERE email=%s",
           (email,)
)

        user = cur.fetchone()
        print("User:", user)

        cur.close()
        conn.close()

        print(user)

        if user:
            print(user[3])
            print(password)

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            # role NULL ho to default user
            print(user)

            if len(user) < 5:
               return f"User tuple has only {len(user)} values: {user}"

            role = user[4]
            session["role"] = role

            if role == "admin":
                return redirect("/admin")
            else:
                return redirect("/dashboard")

        return render_template(
            "login.html",
            error="❌ Invalid Email or Password"
        )

    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO users(fullname, email, password,role)
                VALUES(%s, %s, %s, %s)
            """, (fullname, email, hashed_password, "user"))

            conn.commit()

            return render_template(
                "register.html",
                success="✅ Registration Successful!"
            )

        except Exception as e:
           conn.rollback()

           return render_template(
                "register.html",
                success=f"❌ {e}"
        )

        finally:
           cur.close()
           conn.close()
    return render_template("register.html")   

@app.route("/report", methods=["GET", "POST"])
def report():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        print("====== REPORT RECEIVED ======")

        print(request.form)

        print(request.files)

        fullname = request.form["fullname"]
        mobile = request.form["mobile"]
        address = request.form["address"]
        city = request.form["city"]
        leakage_type = request.form["leakage_type"]
        description = request.form["description"]
        image = request.files["image"]

        # ================= Validation =================

        # Mobile Number
        if not mobile.isdigit() or len(mobile) != 10:
            return render_template(
                "report.html",
                success="❌ Mobile Number must be exactly 10 digits."
            )

        # Name
        if len(fullname.strip()) < 3:
            return render_template(
                "report.html",
                success="❌ Name must be at least 3 characters."
            )

        # ================= Save Image =================
        UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
        app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        print(app.config["UPLOAD_FOLDER"])
        filename = secure_filename(image.filename)

        image.save(
            os.path.join(app.config["UPLOAD_FOLDER"], filename)
        )

        # ================= Database =================

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO reports
        (user_id, fullname, mobile, address, city, leakage_type, description, image)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            fullname,
            mobile,
            address,
            city,
            leakage_type,
            description,
            filename
        ))

        conn.commit()
        cur.close()
        conn.close()
        flash("✅ Report Submitted Successfully!", "success")
        return redirect("/dashboard")

    return render_template("report.html", success="")

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    search = request.args.get("search", "")

    conn = get_db()
    cur = conn.cursor()

    # =======================
    # Dashboard Statistics
    # =======================

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reports")
    total_reports = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reports WHERE status='In Progress'")
    inprogress = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'")
    resolved = cur.fetchone()[0]

    # =======================
    # Search Reports
    # =======================

    query = """
    SELECT id,
           fullname,
           city,
           leakage_type,
           mobile,
           image,
           status,
           created_at
    FROM reports
    WHERE 1=1
    """

    params = []

    if search:
        query += """
        AND (
            fullname LIKE %s
            OR city LIKE %s
            OR mobile LIKE %s
            OR leakage_type LIKE %s
        )
        """

        params.extend([
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ])

    query += " ORDER BY id DESC"

    cur.execute(query, tuple(params))
    reports = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin.html",
        username=session["user_name"],
        total_users=total_users,
        total_reports=total_reports,
        pending=pending,
        inprogress=inprogress,
        resolved=resolved,
        reports=reports,
        search=search
    )
@app.route("/users")
def users():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    search = request.args.get("search", "")

    conn = get_db()
    cur = conn.cursor()

    query = """
    SELECT id, fullname, email, role
    FROM users
    WHERE 1=1
    """

    params = []

    if search:
        query += " AND (fullname LIKE %s OR email LIKE %s)"
        params.append("%" + search + "%")
        params.append("%" + search + "%")

    query += " ORDER BY id DESC"

    cur.execute(query, tuple(params))
    users = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("users.html", users=users, search=search)


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")
    status = request.args.get("status", "")
    sort = request.args.get("sort", "desc")
    date = request.args.get("date", "")

    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    conn = get_db()
    cur = conn.cursor()
    # Total Reports (Current User)
    cur.execute(
       "SELECT COUNT(*) FROM reports WHERE user_id=%s",
        (session["user_id"],)
    )
    total_reports = cur.fetchone()[0]

# Total Users (Admin wali value, isse waise hi rehne do)
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

# Pending Reports (Current User)
    cur.execute(
        "SELECT COUNT(*) FROM reports WHERE user_id=%s AND status='Pending'",
        (session["user_id"],)
    )
    pending_reports = cur.fetchone()[0]

# In Progress Reports (Current User)
    cur.execute(
        "SELECT COUNT(*) FROM reports WHERE user_id=%s AND status='In Progress'",
        (session["user_id"],)
    )
    inprogress_reports = cur.fetchone()[0]

# Resolved Reports (Current User)
    cur.execute(
        "SELECT COUNT(*) FROM reports WHERE user_id=%s AND status='Resolved'",
        (session["user_id"],)
    )
    resolved_reports = cur.fetchone()[0]

# City Wise Reports (Current User)
    cur.execute("""
        SELECT city, COUNT(*)
        FROM reports
        WHERE user_id=%s
        GROUP BY city
        ORDER BY COUNT(*) DESC
    """, (session["user_id"],))
    city_data = cur.fetchall()

# ==========================
# Dynamic Query
# ==========================

    query = """
    SELECT id, fullname, city, leakage_type, mobile,
           image, status, created_at
    FROM reports
    WHERE user_id=%s
    """

    params = [session["user_id"]]

    if search:
        query += " AND (fullname LIKE %s OR city LIKE %s)"
        params.append("%" + search + "%")
        params.append("%" + search + "%")

    if status:
        query += " AND status=%s"
        params.append(status)

    if date:
        query += " AND DATE(created_at)=%s"
        params.append(date)

    if sort == "asc":
        query += " ORDER BY id ASC"
    else:
        query += " ORDER BY id DESC"

    query += " LIMIT %s OFFSET %s"

    params.append(per_page)
    params.append(offset)

    cur.execute(query, tuple(params))
    reports = cur.fetchall()

# ==========================
# Total Pages
# ==========================

    cur.execute(
        "SELECT COUNT(*) FROM reports WHERE user_id=%s",
        (session["user_id"],)
    )
    total = cur.fetchone()[0]

    pages = (total + per_page - 1) // per_page

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        username=session["user_name"],
        total_reports=total_reports,
        total_users=total_users,
        pending_reports=pending_reports,
        inprogress_reports=inprogress_reports,
        resolved_reports=resolved_reports,
        reports=reports,
        city_data=city_data,
        search=search,
        status=status,
        date=date,
        sort=sort,
        page=page,
        pages=pages
    ) 
@app.route("/view/<int:id>")
def view_report(id):

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM reports WHERE id=%s", (id,))
    report = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "view_report.html",
        report=report
    )
@app.route("/delete_user/<int:id>")
def delete_user(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    if id == session["user_id"]:
        flash("You cannot delete your own account.", "error")
        return redirect("/users")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("User Deleted Successfully!", "success")

    return redirect("/users")

@app.route("/delete_report/<int:id>")
def delete_report(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM reports WHERE id=%s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("🗑 Report Deleted Successfully!", "success")

    return redirect("/admin")
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Update Data
    if request.method == "POST":

        fullname = request.form["fullname"]
        mobile = request.form["mobile"]
        address = request.form["address"]
        city = request.form["city"]
        leakage_type = request.form["leakage_type"]
        description = request.form["description"]

        cur.execute("""
            UPDATE reports
            SET fullname=%s,
                mobile=%s,
                address=%s,
                city=%s,
                leakage_type=%s,
                description=%s
            WHERE id=%s
        """, (
            fullname,
            mobile,
            address,
            city,
            leakage_type,
            description,
            id
        ))

        conn.commit()
        cur.close()
        conn.close()
        flash("✏️ Report Updated Successfully!", "success")

        return redirect("/dashboard")

    # Show Existing Data
    cur.execute("SELECT * FROM reports WHERE id=%s", (id,))
    report = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_report.html", report=report)

@app.route("/update_status/<int:report_id>", methods=["POST"])
def update_status(report_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    status = request.form["status"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE reports
        SET status=%s
        WHERE id=%s
        """,
        (status, report_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    flash("✅ Status Updated Successfully!", "success")

    return redirect("/admin")

@app.route("/export_pdf")
def export_pdf():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT fullname, city, leakage_type, mobile, status
        FROM reports
        ORDER BY id DESC
    """)

    reports = cur.fetchall()
    
    cur.close()
    conn.close()

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    data = []

    data.append([
        Paragraph("<b>Name</b>", styles["BodyText"]),
        Paragraph("<b>City</b>", styles["BodyText"]),
        Paragraph("<b>Leakage</b>", styles["BodyText"]),
        Paragraph("<b>Mobile</b>", styles["BodyText"]),
        Paragraph("<b>Status</b>", styles["BodyText"])
    ])

    for report in reports:
        data.append(list(report))

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.green),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
    ]))

    doc.build([table])

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)

    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=Water_Reports.pdf"

    return response

@app.route("/export_excel")
def export_excel():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT fullname, city, leakage_type, mobile, status
        FROM reports
        ORDER BY id DESC
    """)

    reports = cur.fetchall()
    cur.close()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Water Reports"

    # Header
    ws.append([
        "Full Name",
        "City",
        "Leakage Type",
        "Mobile",
        "Status"
    ])

    # Data
    for row in reports:
        ws.append(row)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.getvalue())

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=Smart_Water_Reports.xlsx"

    response.headers[
        "Content-Type"
    ] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response
@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully!", "success")

    return redirect("/login")

@app.route("/testdb")

def testdb():
    try:
        conn = get_db()
        cur = conn.cursor()
        print(conn)

        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        print(cur.fetchone())
        cur.close()
        conn.close()

        return "Database Connected"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e)
    
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]
        new_password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user:

            hashed = generate_password_hash(new_password)

            cur.execute(
                "UPDATE users SET password=%s WHERE email=%s",
                (hashed, email)
            )

            conn.commit()
            cur.close()
            conn.close()

            return render_template(
                "forgot_password.html",
                success="✅ Password Updated Successfully!"
            )

        else:

            cur.close()
            conn.close()

            return render_template(
                "forgot_password.html",
                error="❌ Email Not Found!"
            )

    return render_template("forgot_password.html")     
import csv
from flask import Response

@app.route("/export_csv")
def export_csv():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,
               fullname,
               mobile,
               city,
               leakage_type,
               status,
               created_at
        FROM reports
    """)

    reports = cur.fetchall()

    cur.close()
    conn.close()

    def generate():

        data = csv.writer(open("temp.csv","w"))

        yield "ID,Name,Mobile,City,Leakage,Status,Date\n"

        for row in reports:
            yield ",".join(str(x) for x in row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment;filename=reports.csv"
        }
    )
@app.route("/report/<int:id>")
def report_details():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM reports
        WHERE id=%s
    """, (id,))

    report = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "report_details.html",
        report=report
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
    )

    