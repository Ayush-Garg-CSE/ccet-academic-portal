from flask import Flask, request, render_template, session, redirect, flash, url_for, jsonify
import sqlite3
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configuration for simulated certificate/fee proof uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to connect to SQLite and return dictionary rows
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name like row['title']
    return conn

# --- 1. HOME PORTAL ROUTE ---
@app.route("/")
def dashboard_home():
    conn = get_db_connection()
    # Fetch all notices sorted by newest ID first
    db_notices = conn.execute("SELECT * FROM notices ORDER BY id DESC").fetchall()
    conn.close()
    
    # Only pass the latest 3 notices to the front page frosted card
    return render_template("index.html", latest_notices=db_notices[:3])

# --- 2. MULTI-ROLE LOGIN SYSTEM ---
@app.route("/login", methods=["GET", "POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    conn = get_db_connection()
    # Explicitly pull all structural profile parameters from the database
    user = conn.execute("SELECT email, role, branch, batch, course FROM users WHERE email=? AND password=? AND role=?", (email, password, role)).fetchone()
    conn.close()

    if user:
        # Normalize structural roles into 4 distinct functional authorization tiers
        is_student = (role == "Student")
        is_faculty = role in ["Faculty", "Department Representative"]
        is_exam_unit = role in ["Result Unit", "Assistant Examination"]
        is_admin_officer = role in [
            "Super-Administrator", "Super Administrator", "Branch Administrator", 
            "Nodal Officer", "Branch Assistant", "Academic Clerk", "SO"
        ]

        user_data = {
            "name": email.split("@")[0].replace(".", " ").title(),
            "role": role,
            "email": email,
            "title": f"{role} Control Panel",
            
            # Extract new dynamic profile parameters directly from the fetched database row
            "branch": user[2] if user[2] else "Computer Science & Engineering",
            "batch": user[3] if user[3] else "2025-2029",
            "course": user[4] if user[4] else "B.E.",
            
            "is_student": is_student,
            "is_faculty": is_faculty,
            "is_exam_unit": is_exam_unit,
            "is_admin_officer": is_admin_officer
        }
        session['user_data'] = user_data
        
        # Initialize a default mock registration array tracking for students
        if is_student and 'registrations' not in session:
            session['registrations'] = ["1", "2"] # Semesters 1 & 2 pre-cleared
            
        return redirect(url_for('dashboard'))
    else:
        flash("Access Denied. Invalid credentials or role selection.", "login_error")
        return render_template('login.html')

# --- 3. STUDENT / FACULTY / ADMIN UNIVERSAL DASHBOARD ---
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
    user_data = session.get('user_data')
    if not user_data or not user_data.get('is_admin_officer'):
        flash("Unauthorized administrative operation access blocked.", "error")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        date = request.form.get("date")
        category = request.form.get("category")
        title = request.form.get("title")

        conn = get_db_connection()
        # Insert the brand new announcement row
        conn.execute("INSERT INTO notices (date, title, category) VALUES (?, ?, ?)", (date, title, category))
        conn.commit()
        
        # Check if total notice count exceeds 4 to keep dashboard optimized
        db_notices = conn.execute("SELECT id FROM notices ORDER BY id DESC").fetchall()
        if len(db_notices) > 4:
            old_ids = [row["id"] for row in db_notices[4:]]
            for old_id in old_ids:
                conn.execute("DELETE FROM notices WHERE id = ?", (old_id,))
            conn.commit()
            
        conn.close()
        return redirect("/")
        
    return render_template("admin_notice.html")

# --- 6. FORGOT PASSWORD: STEP 1 (EMAIL VERIFICATION) ---
@app.route("/forgot-password", methods=["GET", "POST"])
@app.route("/forgot_password", methods=["GET", "POST"])
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
@app.route("/reset_password", methods=["GET", "POST"])
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


# 8.--- STUDENT REQUISITION: EXAMINATION PORTAL WITH ONE-TIME ALERTS ---
@app.route("/examination", methods=["GET", "POST"])
def examination():
    user_data = session.get('user_data')
    if not user_data or not user_data.get('is_student'):
        flash("Access Restricted: Section reserved for student workspaces.", "error")
        return redirect(url_for('dashboard'))
        
    if 'branch' not in user_data: user_data['branch'] = "Computer Science & Engineering"
    if 'batch' not in user_data: user_data['batch'] = "2025-2029"
    if 'course' not in user_data: user_data['course'] = "B.E."
    session['user_data'] = user_data

    conn = get_db_connection()

    if request.method == "POST":
        semester = request.form.get("semester")
        amount = request.form.get("amount")
        transaction_id = request.form.get("transaction_id")
        receipt_date = request.form.get("receipt_date")
        file = request.files.get("fee_proof")
        
        if file and file.filename != '' and transaction_id:
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"{user_data['name']}_sem{semester}_{file.filename}")
            receipts_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'receipts')
            os.makedirs(receipts_folder, exist_ok=True)
            file.save(os.path.join(receipts_folder, filename))
            
            try:
                conn.execute("""
                    INSERT INTO exam_submissions 
                    (user_id, student_email, branch, semester, batch, course, amount, transaction_id, receipt_date, receipt_filename, status, notification_seen)
                    VALUES ((SELECT id FROM users WHERE email=?), ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', 1)
                """, (user_data['email'], user_data['email'], user_data['branch'], int(semester), user_data['batch'], user_data['course'], int(amount), transaction_id, receipt_date, filename))
                conn.commit()
                flash(f"Success! Requisition for Semester {semester} Exam successfully registered.", "success")
            except Exception as e:
                flash("Submission Failed: Transaction ID already uploaded.", "error")
            finally:
                conn.close()
            return redirect(url_for('examination'))
            
    # --- ONE-TIME NOTIFICATION CHECK ENGINE ---
    unread_decision = conn.execute("""
        SELECT id, semester, status 
        FROM exam_submissions 
        WHERE student_email = ? AND notification_seen = 0 AND status IN ('Approved', 'Rejected')
    """, (user_data['email'],)).fetchone()
    
    if unread_decision:
        if unread_decision['status'] == 'Approved':
            flash(f"🎉 Your examination form submission for Semester {unread_decision['semester']} has been APPROVED by the Administration!", "success")
        else:
            flash(f"❌ Your examination form submission for Semester {unread_decision['semester']} was REJECTED. Please re-verify fee proof details.", "error")
            
        conn.execute("UPDATE exam_submissions SET notification_seen = 1 WHERE id = ?", (unread_decision['id'],))
        conn.commit()

    submission_history = conn.execute("SELECT semester, status FROM exam_submissions WHERE student_email = ?", (user_data['email'],)).fetchall()
    conn.close()

    status_map = {str(row['semester']): row['status'] for row in submission_history}
    return render_template("examination.html", user=user_data, status_map=status_map)

# --- ADMINISTRATIVE WORKSPACE: PRINTABLE ADMIT CARD ENGINE ---
@app.route("/examination/admit-card/<int:semester>", methods=["GET"])
def download_admit_card(semester):
    user_data = session.get('user_data')
    if not user_data:
        flash("Authorization Required: Please re-authenticate system session.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    # 1. Verify this student's request is approved for this semester before opening access
    row = conn.execute("""
        SELECT branch, course, status 
        FROM exam_submissions 
        WHERE student_email = ? AND semester = ?
    """, (user_data['email'], semester)).fetchone()

    # Security check: If they haven't applied or were not approved, deny access
    if not row or row['status'] != 'Approved':
        conn.close()
        flash("Access Denied: Your admit card remains locked until an administrative officer approves your fee submission proof.", "error")
        return redirect(url_for('examination'))

    # CONVERT SQLite Row to a standard Python Dict to prevent Jinja property reference crashes
    sub_info = dict(row)

    # Normalize database query branch mapping fields
    db_branch = sub_info['branch']
    if db_branch == "CSE": db_branch = "Computer Science & Engineering"
    elif db_branch == "Mechanical": db_branch = "Mech"

    # 2. Fetch the subject data for this specific semester and branch
    subjects_rows = conn.execute("""
        SELECT subject, subject_type, credits 
        FROM syllabus 
        WHERE branch = ? AND semester = ?
    """, (db_branch, semester)).fetchall()
    
    subjects = [dict(r) for r in subjects_rows]
    conn.close()

    return render_template("admit_card.html", user=user_data, semester=semester, sub_info=sub_info, subjects=subjects)
# --- 8b. CLEAN & SEPERATED ADMIN SUBMISSION VERIFICATION PANEL ---
@app.route("/admin/verify-submissions", methods=["GET", "POST"])
def admin_verify_submissions():
    conn = get_db_connection()

    if request.method == "POST":
        submission_id = request.form.get("submission_id")
        action = request.form.get("action")  # 'Approved' or 'Rejected'
        
        conn.execute("""
            UPDATE exam_submissions 
            SET status = ?, notification_seen = 0 
            WHERE id = ?
        """, (action, submission_id))
        conn.commit()
        flash(f"Submission record successfully processed.", "success")
        return redirect(url_for('admin_verify_submissions'))

    # ONLY fetch 'Pending' submissions so completed ones disappear from the queue instantly!
    submissions = conn.execute("""
        SELECT id, student_email, branch, semester, course, amount, transaction_id, receipt_date, receipt_filename, status, submission_timestamp 
        FROM exam_submissions 
        WHERE status = 'Pending'
        ORDER BY submission_timestamp DESC
    """).fetchall()
    conn.close()

    user_data = session.get('user_data', {"name": "Developer Mode", "role": "Administrator"})
    return render_template("admin_verify.html", user=user_data, submissions=submissions)


# --- NEW ADDITION: EXAMINATION MATRIX DATA RETRIEVAL API ---
@app.route("/api/fetch-examination-matrix", methods=["GET"])
def fetch_examination_matrix():
    branch = request.args.get("branch")
    semester = request.args.get("semester")
    
    if not branch or not semester:
        return jsonify({"subjects": [], "error": "Missing selection criteria attributes"}), 400
        
    if branch == "CSE":
        branch = "Computer Science & Engineering"
    elif branch == "Mechanical":
        branch = "Mech"

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT subject, subject_type, credits 
        FROM syllabus 
        WHERE branch = ? AND semester = ?
    """, (branch, int(semester)))
    
    rows = cursor.fetchall()
    conn.close()
    
    subjects_list = []
    for r in rows:
        subjects_list.append({
            "subject": r[0],
            "subject_type": r[1],
            "credits": r[2]
        })
        
    return jsonify({"subjects": subjects_list})
# --- UNIVERSITY CERTIFICATE TRACKING SYSTEM ---
@app.route("/api/request-certificate", methods=["POST"])
def request_certificate():
    # Attempt to grab student from direct or nested session configurations
    email = session.get('email') or (session.get('user_data', {}).get('email') if session.get('user_data') else None)
    
    if not email:
        return jsonify({"success": False, "message": "Session expired. Please log in again."}), 401
    
    conn = get_db_connection()
    
    # Verify if they have at least one 'Approved' examination submission before issuing a graduation token
    approval_check = conn.execute("""
        SELECT COUNT(*) as count FROM exam_submissions 
        WHERE student_email = ? AND status = 'Approved'
    """, (email,)).fetchone()
    
    conn.close()
    
    if approval_check['count'] == 0:
        return jsonify({
            "success": False, 
            "message": "Clearance Denied: You must have at least one verified/approved semester record to request a Provisional Certificate."
        })
    
    return jsonify({
        "success": True, 
        "message": "Clearance Granted! Preparing your verified document pack..."
    })


@app.route("/examination/download-certificate", methods=["GET"])
def download_certificate():
    email = session.get('email')
    name = session.get('name', 'Bona fide Student')
    user_id = session.get('user_id', 101)
    
    # Nested session fallback check
    if not email and session.get('user_data'):
        email = session['user_data'].get('email')
        name = session['user_data'].get('name', name)
        user_id = session['user_data'].get('id', user_id)

    if not email:
        return "Authorization Required. Please log in first.", 403
        
    user_pack = {'email': email, 'name': name, 'id': user_id}
    
    from datetime import datetime
    generation_date = datetime.now().strftime("%B %d, %Y")
    
    return render_template("certificate_template.html", user=user_pack, date=generation_date)

# --- 9. WORK-FLOW ROUTE (SHARED BY FACULTY & ADMINISTRATIVE BRANCHES) ---
@app.route("/workflow", methods=["GET", "POST"])
def workflow():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
        
    # Block unauthorized student or evaluation tier entries
    if user_data.get('is_student') or user_data.get('is_exam_unit'):
        flash("Access Denied to system workflow registries.", "error")
        return redirect(url_for('dashboard'))

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
# --- 10. RESULT ROUTE (INTEGRATED STUDENT PIPELINE) ---
@app.route("/result", methods=["GET", "POST"])
def result():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
        
    # --- GET REQUEST: Loads selection profile ---
    if request.method == "GET":
        # Pull profile directly from database to ensure fresh string matching
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        db_user = conn.execute("SELECT * FROM users WHERE email=?", (user_data.get('email'),)).fetchone()
        conn.close()

        if db_user:
            b = db_user['branch'] if db_user['branch'] else ''
            if "computer" in b.lower() or b == "CSE":
                user_data['branch_full'] = "Computer Science & Engineering"
            elif "mech" in b.lower() or b == "ME":
                user_data['branch_full'] = "Mechanical Engineering"
            elif "ece" in b.lower() or b == "EE" or "electron" in b.lower():
                user_data['branch_full'] = "Electronics & Communication Engineering"
            elif "civil" in b.lower():
                user_data['branch_full'] = "Civil Engineering"
            else:
                user_data['branch_full'] = b
        else:
            user_data['branch_full'] = "Not Assigned"
            
        return render_template("result.html", user=user_data)

   # --- POST REQUEST: Process Selection ---
    selected_semester = int(request.form.get('semester'))
    current_user_email = user_data.get('email')

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Re-verify branch full metadata for the view page
    db_user = cursor.execute("SELECT branch FROM users WHERE email=?", (current_user_email,)).fetchone()
    b_string = db_user['branch'] if (db_user and db_user['branch']) else ''
    
    if "computer" in b_string.lower() or b_string == "CSE":
        user_data['branch_full'] = "Computer Science & Engineering"
    elif "mech" in b_string.lower() or b_string == "ME":
        user_data['branch_full'] = "Mechanical Engineering"
    elif "ece" in b_string.lower() or b_string == "EE" or "electron" in b_string.lower():
        user_data['branch_full'] = "Electronics & Communication Engineering"
    elif "civil" in b_string.lower():
        user_data['branch_full'] = "Civil Engineering"
    else:
        user_data['branch_full'] = b_string

    result_record = cursor.execute(
        "SELECT * FROM student_results WHERE student_email=? AND semester=?", 
        (current_user_email, selected_semester)
    ).fetchone()

    # --- FIXED SNIPPET ---
    if not result_record:
        conn.close()
        flash(f"Result for Semester {selected_semester} has not been declared yet.", "warning")
        return redirect(url_for('result'))
    # ---------------------

    result_dict = dict(result_record)
    parsed_subjects = json.loads(result_dict['subjects_json'])

    if selected_semester % 2 == 0:
        previous_sem = selected_semester - 1
        prev_record = cursor.execute(
            "SELECT sgpa FROM student_results WHERE student_email=? AND semester=?", 
            (current_user_email, previous_sem)
        ).fetchone()
        
        if prev_record:
            result_dict['calculated_cgpa'] = (prev_record['sgpa'] + result_dict['sgpa']) / 2
            result_dict['has_yearly_cgpa'] = True
        else:
            result_dict['calculated_cgpa'] = result_dict['sgpa']
            result_dict['has_yearly_cgpa'] = False
    else:
        result_dict['has_yearly_cgpa'] = False

    conn.close()

    return render_template(
        "view_result.html", 
        user=user_data, 
        result=result_dict, 
        subjects=parsed_subjects,
        semester=selected_semester
    )
#---Result Calculation and upload---
import csv
import json
import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for, session



# --- 1. BULK SPREADSHEET ENGINE ROUTE ---
@app.route("/upload_results", methods=["GET", "POST"])
def upload_results():
    if 'user_data' not in session:
        return redirect("/")

    if request.method == "GET":
        return render_template("upload_results.html")

    selected_session = request.form.get('session')
    selected_semester = int(request.form.get('semester'))
    
    if 'spreadsheet' not in request.files:
        flash("No file detected.", "danger")
        return redirect(request.url)
        
    file = request.files['spreadsheet']
    if file.filename == '' or not file.filename.endswith('.csv'):
        flash("Please upload a valid .csv spreadsheet.", "danger")
        return redirect(request.url)

    # Official CCET / Panjab University Letter Grade Weights
    GRADE_MAP = {
        'A+': 10, 'A': 9, 'B+': 8, 'B': 7, 'C+': 6, 'C': 5, 'D': 4, 'F': 0
    }

    stream = file.stream.read().decode("utf-8").splitlines()
    csv_reader = csv.DictReader(stream)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    success_count = 0

    for row in csv_reader:
        email = row.get('email')
        if not email:
            continue

        subjects_list = []
        total_earned_points = 0.0
        total_credits = 0.0
        i = 1

        while True:
            code_key = f'sub{i}_code'
            name_key = f'sub{i}_name'
            credits_key = f'sub{i}_credits'
            grade_key = f'sub{i}_grade'
            
            if code_key not in row or not row[code_key]:
                break  # End of row data structure arrays
                
            grade_letter = row[grade_key].strip().upper()
            try:
                credits_val = float(row[credits_key])
            except (ValueError, TypeError):
                credits_val = 0.0

            subjects_list.append({
                "code": row[code_key],
                "name": row[name_key],
                "credits": credits_val,
                "grade": grade_letter
            })

            # Audit grades (S, X, NP, NF) are skipped here since they are missing from GRADE_MAP
            if grade_letter in GRADE_MAP:
                total_earned_points += (credits_val * GRADE_MAP[grade_letter])
                total_credits += credits_val

            i += 1

        # Math logic formulation
        calculated_sgpa = (total_earned_points / total_credits) if total_credits > 0 else 0.0
        subjects_json = json.dumps(subjects_list)

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO student_results (student_email, semester, subjects_json, sgpa, cgpa)
                VALUES (?, ?, ?, ?, ?)
            """, (email, selected_semester, subjects_json, round(calculated_sgpa, 2), round(calculated_sgpa, 2)))
            
            cursor.execute("UPDATE users SET batch=? WHERE email=?", (selected_session, email))
            success_count += 1
        except Exception as e:
            print(f"Database row ingestion fault: {e}")

    conn.commit()
    conn.close()

    flash(f"Successfully compiled ledger! Calculated SGPAs for {success_count} student records.", "success")
    return redirect(url_for('upload_results'))

# --- 11. ATTENDANCE ROUTE (BRANCHED BY ACCESSIBLE TIERS) ---
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    user_data = session.get('user_data')
    if not user_data:
        return redirect("/")
        
    if user_data.get('is_student'):
        return render_template("attendance.html", user=user_data, action="student_view")

    if not user_data.get('is_faculty'):
        flash("Attendance systems are restricted to faculty workspaces.", "error")
        return redirect(url_for('dashboard'))

    action = request.args.get("action")
    monthly_data = []
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":
        if action == "register":
            roll_no = request.form.get("roll_no")
            date = request.form.get("date")
            status = request.form.get("status")
            cursor.execute("INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)", (roll_no, date, status))
            conn.commit()
            flash(f"Attendance marked successfully for {roll_no}.", "success")
            conn.close()
            return redirect("/attendance?action=register")

        elif action == "upload":
            flash("File processing completed successfully.", "success")
            conn.close()
            return redirect("/attendance?action=upload")

        elif action == "archive":
            archive_date = request.form.get("archive_date")
            cursor.execute("UPDATE attendance SET archived=1 WHERE date < ?", (archive_date,))
            conn.commit()
            flash(f"Records archived successfully.", "success")
            conn.close()
            return redirect("/attendance?action=archive")

        elif action == "finalize":
            finalize_month = request.form.get("finalize_month")
            cursor.execute("UPDATE attendance SET finalized=1 WHERE strftime('%m', date)=?", (finalize_month,))
            conn.commit()
            flash(f"Attendance finalized for month {finalize_month}.", "success")
            conn.close()
            return redirect("/attendance?action=finalize")

        elif action == "delete":
            record_id = request.form.get("id")
            cursor.execute("DELETE FROM attendance WHERE id=?", (record_id,))
            conn.commit()
            conn.close()
            return redirect("/attendance?action=monthly")

    if action == "monthly":
        month = request.args.get("month")
        if month:
            cursor.execute("SELECT id, roll_no, date, status FROM attendance WHERE strftime('%m', date)=?", (month,))
            monthly_data = cursor.fetchall()

    conn.close()
    return render_template("attendance.html", user=user_data, action=action, monthly_data=monthly_data)

# --- 12. SYLLABUS TRACKING PANELS ---
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
            print("Notice: 'syllabus' table missing from database setup.")
        finally:
            if 'conn' in locals(): conn.close()

    return render_template("syllabus.html", user=user_data, action=action, syllabus_data=syllabus_data)

# --- 13. AUXILIARY CHANNELS AND DOCUPLOAD POOLS ---
@app.route("/docupload")
def docupload():
    user_data = session.get('user_data')
    if not user_data or not user_data.get('is_student'):
        flash("Document uploads are limited to student file registration pools.", "error")
        return redirect(url_for('dashboard'))
        
    document = {
        "title": "Student Internship Approval Form",
        "issued_by": "Panjab University Academic Cell",
        "date": "12 June 2026",
        "content": "This document certifies that the student has been approved to process internship credentials."
    }
    return render_template("docupload.html", user=user_data, document=document)

# --- 14. EXAMINING SPECIALIZED ENDPOINTS ---
@app.route("/exam-control/datesheets")
@app.route("/exam-control/discrepancies")
def exam_control_subpages():
    user_data = session.get('user_data')
    if not user_data or not user_data.get('is_exam_unit'):
        flash("Unauthorized Controller Action.", "error")
        return redirect(url_for('dashboard'))
    return f"<h1>⚖️ Examination Control - {user_data['role']} Session Roster</h1>"

# --- 15. SYSTEM ACCOUNT SETTINGS ---
@app.route("/settings", methods=["GET", "POST"])
def settings():
    user_data = session.get('user_data')
    if not user_data: return redirect("/")

    action = request.args.get("action")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":
        if action == "password":
            current_pwd = request.form.get("current_password")
            new_pwd = request.form.get("new_password")
            confirm_pwd = request.form.get("confirm_password")

            cursor.execute("SELECT password FROM users WHERE email=?", (user_data["email"],))
            result = cursor.fetchone()
            if result and current_pwd == result[0] and new_pwd == confirm_pwd:
                cursor.execute("UPDATE users SET password=? WHERE email=?", (new_pwd, user_data["email"]))
                conn.commit()
                flash("Password updated successfully!", "success")
            else:
                flash("Password matching or verification failure.", "error")
                
        elif action == "profile":
            new_name = request.form.get("name")
            if new_name:
                user_data["name"] = new_name.capitalize()
                session["user_data"] = user_data
                flash("Profile name updated successfully!", "success")

    profile_info = {"email": user_data["email"], "phone": ""}
    conn.close()
    return render_template("settings.html", user=user_data, action=action, profile=profile_info)

# --- 16. LOGOUT TERMINATION CONTROL ---
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect("/")
# Automatically generates the upload directory if it's missing from your static folder
os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
if __name__ == "__main__":
    app.run(debug=True)

            