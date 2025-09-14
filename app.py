import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

# 优先从 DATABASE_URL 读取；如果没有，则从单独变量拼接（两种方式都支持）
db_url = os.getenv("DATABASE_URL")
if not db_url:
    user = os.getenv("MYSQLUSER", "root")
    password = os.getenv("MYSQLPASSWORD", "")
    host = os.getenv("MYSQLHOST", "127.0.0.1")
    port = os.getenv("MYSQLPORT", "3306")
    database = os.getenv("MYSQLDATABASE", "railway")
    db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(db_url, pool_pre_ping=True, echo=False)

# 首页：员工列表
@app.route("/")
def index():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, age, department FROM employee ORDER BY id DESC"))
        employees = [dict(r._mapping) for r in rows]
    return render_template("employees.html", employees=employees)

# API：返回员工 JSON
@app.route("/api/employees")
def api_employees():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, age, department FROM employee ORDER BY id DESC"))
        employees = [dict(r._mapping) for r in rows]
    return jsonify(employees)

# 新增员工页面
@app.route("/employees/new")
def employee_new():
    return render_template("employee_new.html")

# 提交新增员工
@app.route("/employees/create", methods=["POST"])
def employee_create():
    name = request.form.get("name", "").strip()
    age = request.form.get("age", "").strip()
    department = request.form.get("department", "").strip()

    if not name or not age or not department:
        # 简单的兜底校验；生产可以换成闪现消息
        return "Missing fields", 400

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO employee (name, age, department) VALUES (:name, :age, :department)"),
            {"name": name, "age": int(age), "department": department},
        )
    return redirect(url_for("index"))

# （可选）删除员工
@app.route("/employees/<int:emp_id>/delete", methods=["POST"])
def employee_delete(emp_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM employee WHERE id = :id"), {"id": emp_id})
    return redirect(url_for("index"))

if __name__ == "__main__":
    # 直接运行：python app.py
    app.run(debug=True)
