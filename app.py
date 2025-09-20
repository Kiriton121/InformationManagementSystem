import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from sqlalchemy import create_engine, text
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

# -----------------------------
# 环境变量 & DB 连接
# -----------------------------
load_dotenv()

# 优先读取完整连接串（如果将来用 DATABASE_URL 直接托管也行）
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # 用 Railway 的五段式变量拼接
    MYSQLUSER = os.getenv("MYSQLUSER")
    MYSQLPASSWORD = os.getenv("MYSQLPASSWORD")
    MYSQLHOST = os.getenv("MYSQLHOST")
    MYSQLPORT = os.getenv("MYSQLPORT", "3306")
    MYSQLDATABASE = os.getenv("MYSQLDATABASE")
    # 注意：使用 PyMySQL 驱动
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQLUSER}:{MYSQLPASSWORD}"
        f"@{MYSQLHOST}:{MYSQLPORT}/{MYSQLDATABASE}"
    )

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True,
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


# -----------------------------
# 工具：需要管理员登录
# -----------------------------
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("请先以管理员身份登录。", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# -----------------------------
# 首页：身份选择（员工录入 / 管理员登录）
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# -----------------------------
# 管理员登录
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd = request.form.get("password", "").strip()

        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT password_hash FROM admin WHERE username=:u"),
                {"u": uname},
            ).mappings().first()

        if row and check_password_hash(row["password_hash"], pwd):
            session.permanent = True
            session["is_admin"] = True
            session["admin_name"] = uname
            flash("登录成功！", "success")
            return redirect(url_for("list_employees"))
        else:
            flash("用户名或密码错误。", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()   # 清空登录状态
    flash("您已退出登录", "info")
    return redirect(url_for("index"))


# -----------------------------
# 员工列表（仅管理员可见）+ 删除
# -----------------------------
@app.route("/employees", methods=["GET"])
@admin_required
def list_employees():
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, name, age, city, works_url, contact "
                "FROM employee ORDER BY id DESC"
            )
        ).mappings().all()

    return render_template("employees.html", rows=rows)


@app.route("/employees/<int:emp_id>/delete", methods=["POST"])
@admin_required
def delete_employee(emp_id: int):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM employee WHERE id=:i"), {"i": emp_id})
    flash("已删除该记录。", "info")
    return redirect(url_for("list_employees"))


# -----------------------------
# 员工录入（任何人可访问）
# -----------------------------
@app.route("/employees/new", methods=["GET", "POST"])
def employee_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        city = request.form.get("city", "").strip()
        works_url = request.form.get("works_url", "").strip()
        contact = request.form.get("contact", "").strip()

        # 简单校验（可按需补充）
        if not name or not age or not city:
            flash("姓名、年龄、常驻城市为必填项。", "warning")
            return render_template("employee_new.html")

        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO employee (name, age, city, works_url, contact) "
                    "VALUES (:name, :age, :city, :works_url, :contact)"
                ),
                {
                    "name": name,
                    "age": int(age),
                    "city": city,
                    "works_url": works_url or None,
                    "contact": contact or None,
                },
            )
        # 提交完成页
        return redirect(url_for("submitted"))

    return render_template("employee_new.html")


# 提交完成页
@app.route("/submitted", methods=["GET"])
def submitted():
    return render_template("submitted.html")


# -----------------------------
# JSON 调试接口（保留）
# -----------------------------
@app.route("/api/employees", methods=["GET"])
def api_employees():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, age, city, works_url, contact FROM employee ORDER BY id DESC")
        ).mappings().all()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True)
