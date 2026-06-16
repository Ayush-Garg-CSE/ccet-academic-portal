from flask import Flask, request, render_template, session, redirect, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email, password, role))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_data = {
            "name": email.split("@")[0].capitalize(),
            "role": role,
            "email": email,
            "title": f"{role} Dashboard"
        }
        session['user_data'] = user_data
        return render_template("dashboard.html", user=user_data)
    else:
        return "Access Denied. Invalid credentials or role."

@app.route("/dashboard")
def dashboard():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")  # redirect to login if not logged in
    return render_template("dashboard.html", user=user_data)

# -------------------------
# Workflow page
# -------------------------
@app.route("/workflow", methods=["GET", "POST"])
def workflow():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
    action = request.args.get("action")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":
        if action == "assign":
            department = request.form.get("department")
            batch = request.form.get("batch")
            course = request.form.get("course")
            semester = request.form.get("semester")
            subject_type = request.form.get("subject_type")
            subject = request.form.get("subject")

            cursor.execute("""
                INSERT INTO assigned_subjects (department, batch, course, semester, subject_type, subject, faculty_email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (department, batch, course, semester, subject_type, subject, user_data["email"]))
            conn.commit()

        elif action == "delete":
            subject_id = request.form.get("id")
            cursor.execute("DELETE FROM assigned_subjects WHERE rowid=?", (subject_id,))
            conn.commit()

    subjects = []
    if action == "view":
        cursor.execute("SELECT department, batch, course, semester, subject_type, subject, rowid FROM assigned_subjects")
        subjects = cursor.fetchall()

    conn.close()
    return render_template("workflow.html", user=user_data, action=action, subjects=subjects)

# -------------------------
# Result page
# -------------------------
@app.route("/result", methods=["GET", "POST"])
def result():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
    action = request.args.get("action")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    student = None
    results = []

    if action == "fetch" and request.method == "POST":
        roll_no = request.form.get("roll_no")
        branch = request.form.get("branch")
        semester = request.form.get("semester")
        session_val = request.form.get("session")

        cursor.execute("SELECT * FROM students WHERE roll_no=? AND branch=? AND semester=? AND session=?",
                       (roll_no, branch, semester, session_val))
        student = cursor.fetchone()

        if student:
            cursor.execute("SELECT subject, marks, grade FROM marks WHERE roll_no=?", (roll_no,))
            results = cursor.fetchall()

        conn.close()
        return render_template("result.html", user=user_data, action="view", student=student, results=results)

    elif action == "view":
        roll_no = request.args.get("roll_no")
        branch = request.args.get("branch")

        if roll_no and branch:
            cursor.execute("SELECT * FROM students WHERE roll_no=? AND branch=?", (roll_no, branch))
            student = cursor.fetchone()
            if student:
                cursor.execute("SELECT subject, marks, grade FROM marks WHERE roll_no=?", (roll_no,))
                results = cursor.fetchall()

        conn.close()
        return render_template("result.html", user=user_data, action="view", student=student, results=results)

    conn.close()
    return render_template("result.html", user=user_data, action=action)

# -------------------------
# Attendance page
# -------------------------
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
    action = request.args.get("action")
    monthly_data = []

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":
        if action == "register":
            roll_no = request.form.get("roll_no")
            date = request.form.get("date")
            status = request.form.get("status")
            cursor.execute("INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)",
                           (roll_no, date, status))
            conn.commit()
            flash(f"Attendance marked for {roll_no} on {date}", "success")
            conn.close()
            return redirect("/attendance?action=register")

        elif action == "upload":
            file = request.files["file"]
            flash("File uploaded successfully", "success")
            conn.close()
            return redirect("/attendance?action=upload")

        elif action == "archive":
            archive_date = request.form.get("archive_date")
            cursor.execute("UPDATE attendance SET archived=1 WHERE date < ?", (archive_date,))
            conn.commit()
            flash(f"Records archived before {archive_date}", "success")
            conn.close()
            return redirect("/attendance?action=archive")

        elif action == "finalize":
            finalize_month = request.form.get("finalize_month")
            cursor.execute("UPDATE attendance SET finalized=1 WHERE strftime('%m', date)=?", (finalize_month,))
            conn.commit()
            flash(f"Attendance finalized for month {finalize_month}", "success")
            conn.close()
            return redirect("/attendance?action=finalize")

        elif action == "delete":
            record_id = request.form.get("id")
            cursor.execute("DELETE FROM attendance WHERE id=?", (record_id,))
            conn.commit()
            flash(f"Attendance record {record_id} deleted", "success")
            conn.close()
            return redirect("/attendance?action=monthly")

    if action == "monthly":
        month = request.args.get("month")
        if month:
            cursor.execute("""SELECT id, roll_no, date, status
                              FROM attendance
                              WHERE strftime('%m', date)=?""", (month,))
            monthly_data = cursor.fetchall()
            flash("Monthly report generated", "info")

    conn.close()
    return render_template("attendance.html", user=user_data, action=action, monthly_data=monthly_data)

# -------------------------
# Syllabus page
# -------------------------
@app.route("/syllabus")
def syllabus():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")

    action = request.args.get("action")   # <-- capture ?action=view
    syllabus_data = []

    if action == "view":
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT branch, semester, subject FROM syllabus")
            syllabus_data = cursor.fetchall()
        except sqlite3.OperationalError:
            print("Notice: 'syllabus' table not found in database.")
        finally:
            if 'conn' in locals():
                conn.close()

    return render_template("syllabus.html", user=user_data, action=action, syllabus_data=syllabus_data)


# -------------------------
# DocUpload page
# -------------------------
@app.route("/docupload")
def docupload():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
    document = {
        "title": "Student Internship Approval Form",
        "issued_by": "Panjab University Academic Cell",
        "date": "12 June 2026",
        "content": "This document certifies that the student has been approved to undertake a summer internship program at XYZ Tech Solutions Pvt. Ltd. The internship will run from July 1st to August 31st, 2026. The student is expected to submit a detailed report upon completion."
    }
    return render_template("docupload.html", user=user_data, document=document)


# -------------------------
# Settings Page
# -------------------------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    user_data = session.get('user_data')

    if not user_data:
        return redirect("/")

    action = request.args.get("action")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":

        # CHANGE PASSWORD
        if action == "password":

            current_pwd = request.form.get("current_password")
            new_pwd = request.form.get("new_password")
            confirm_pwd = request.form.get("confirm_password")

            cursor.execute(
                "SELECT password FROM users WHERE email=?",
                (user_data["email"],)
            )

            result = cursor.fetchone()

            if result:

                db_password = result[0]

                if current_pwd != db_password:
                    flash("Incorrect current password!", "error")

                elif new_pwd != confirm_pwd:
                    flash("New passwords do not match!", "error")

                else:
                    cursor.execute(
                        "UPDATE users SET password=? WHERE email=?",
                        (new_pwd, user_data["email"])
                    )

                    conn.commit()

                    flash(
                        "Password updated successfully!",
                        "success"
                    )

            conn.close()
            return redirect("/settings?action=password")

        # UPDATE PROFILE
        elif action == "profile":

            new_name = request.form.get("name")

            if new_name:

                user_data["name"] = new_name.capitalize()

                session["user_data"] = user_data

                flash(
                    "Profile updated successfully!",
                    "success"
                )

            conn.close()
            return redirect("/settings?action=profile")

    profile_info = {
        "email": user_data["email"],
        "phone": ""
    }

    conn.close()

    return render_template(
        "settings.html",
        user=user_data,
        action=action,
        profile=profile_info
    )
#-------
#Log Out
#-------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect("/")
                    
if __name__ == "__main__":
    app.run(debug=True)

