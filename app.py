from flask import Flask, request, render_template, session, redirect, flash, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Helper function to connect to SQLite and return dictionary rows
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name like row['title']
    return conn

# --- 1. HOME PORTAL ROUTE ---
@app.route("/")
def home():
    conn = get_db_connection()
    # Fetch all notices sorted by newest ID first
    db_notices = conn.execute("SELECT * FROM notices ORDER BY id DESC").fetchall()
    conn.close()
    
    # Only pass the latest 3 notices to the front page frosted card
    return render_template("index.html", latest_notices=db_notices[:3])

# --- 2. LOGIN SYSTEM ---
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email, password, role)).fetchone()
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
        # 1. Flash the error message into the session
        flash("Access Denied. Invalid credentials or role.", "login_error")
        # 2. Redirect back to the homepage so they stay on the same screen
        return redirect(url_for('home'))

# --- 3. STUDENT / FACULTY DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")  
    return render_template("dashboard.html", user=user_data)

# --- 4. SEE ALL NOTICES PAGE ---
@app.route("/all-notices")
def all_notices():
    conn = get_db_connection()
    db_notices = conn.execute("SELECT * FROM notices ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("all_notices.html", total_notices=db_notices)


# --- 5. AUTOMATED LIVE UPDATES ADMIN PANEL ---
@app.route("/admin/add-notice", methods=["GET", "POST"])
def add_notice():
    if request.method == "POST":
        date = request.form.get("date")
        category = request.form.get("category")
        title = request.form.get("title")

        conn = get_db_connection()
        
        # 1. Insert the brand new announcement row
        conn.execute("INSERT INTO notices (date, title, category) VALUES (?, ?, ?)", (date, title, category))
        conn.commit()
        
        # 2. Check if total notice count exceeds 4
        db_notices = conn.execute("SELECT id FROM notices ORDER BY id DESC").fetchall()
        
        if len(db_notices) > 4:
            # Gather all IDs beyond the newest 4 and delete them permanently
            old_ids = [row["id"] for row in db_notices[4:]]
            for old_id in old_ids:
                conn.execute("DELETE FROM notices WHERE id = ?", (old_id,))
            conn.commit()
            
        conn.close()
        return redirect("/") # Redirect back to home to instantly view changes!
        
    # If GET request, render the separated admin HTML template file instead
    return render_template("admin_notice.html")

# --- 6. FORGOT PASSWORD: STEP 1 (EMAIL VERIFICATION) ---
@app.route("/forgot-password", methods=["GET", "POST"])
@app.route("/forgot_password", methods=["GET", "POST"]) # Handles both dash and underscore versions!
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user:
            session['reset_email'] = email
            return redirect(url_for('reset_password'))
        else:
            flash("This email is not registered in our campus database.", "login_error")
            return redirect(url_for('forgot_password'))
            
    return render_template("forgot_password.html")


# --- 7. FORGOT PASSWORD: STEP 2 (DATABASE OVERWRITE) ---
@app.route("/reset-password", methods=["GET", "POST"])
@app.route("/reset_password", methods=["GET", "POST"]) # Handles both dash and underscore versions!
def reset_password():
    if 'reset_email' not in session:
        return redirect(url_for('home'))
        
    if request.method == "POST":
        new_password = request.form.get("password")
        email = session['reset_email']
        
        conn = get_db_connection()
        conn.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()
        conn.close()
        
        session.pop('reset_email', None)
        flash("Password updated successfully! Please login with your new credentials.", "success")
        return redirect(url_for('home'))
        
    return render_template("reset_password.html")

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

    action = request.args.get("action")   
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

# --- THE EXECUTION CONTEXT BLOCK BELONGS AT THE VERY END ---
if __name__ == "__main__":
    app.run(debug=True)

