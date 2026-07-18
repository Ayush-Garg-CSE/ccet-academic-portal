import sqlite3
import json

def setup_database():
    # Open EXACTLY ONE connection for the entire script run
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    print("Initializing Database Structure...")

    # 1. Create table for users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        branch TEXT DEFAULT NULL,
        batch TEXT DEFAULT NULL,
        course TEXT DEFAULT NULL
    )
    """)

    # 2. Create table for exam_submissions (FIXED: Permanently contains notification_seen)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            student_email TEXT NOT NULL,
            branch TEXT NOT NULL,
            semester INTEGER NOT NULL,
            batch TEXT NOT NULL,
            course TEXT NOT NULL,
            amount INTEGER NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            receipt_date TEXT NOT NULL,
            receipt_filename TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            notification_seen INTEGER DEFAULT 0,  -- <-- PERMANENT COLUMN FIX
            submission_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # 3. Create table for student_results
    cursor.execute("""
CREATE TABLE IF NOT EXISTS student_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_email TEXT NOT NULL,
    semester INTEGER NOT NULL,
    subjects_json TEXT NOT NULL,
    sgpa REAL NOT NULL,
    cgpa REAL NOT NULL,
    UNIQUE(student_email, semester)
)
""")

    # 4. Create the notices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL
        )
    ''')

    # 5. Create core system tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assigned_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department TEXT NOT NULL,
        batch TEXT NOT NULL,
        course TEXT NOT NULL,
        semester TEXT NOT NULL,
        subject_type TEXT NOT NULL,
        subject TEXT NOT NULL,
        faculty_email TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        branch TEXT NOT NULL,
        semester INTEGER NOT NULL,
        session TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT NOT NULL,
        subject TEXT NOT NULL,
        marks INTEGER NOT NULL,
        grade TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT CHECK(status IN ('Present','Absent')),
        archived INTEGER DEFAULT 0,
        finalized INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        category TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syllabus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch TEXT NOT NULL,
        semester INTEGER NOT NULL,
        subject TEXT NOT NULL,
        subject_type TEXT DEFAULT 'Theory',
        credits INTEGER DEFAULT 4
    )
    """)

    print("Seeding baseline records and matrix layouts...")


    # Populate Notices if empty
    cursor.execute("SELECT COUNT(*) FROM notices")
    if cursor.fetchone()[0] == 0:
        initial_notices = [
            ("2026-06-19", "End Semester Examination Schedule Out", "Academic"),
            ("2026-06-18", "Registration open for Tech-Fest 2026", "Event"),
            ("2026-06-15", "Hostel Mess Timings Updated for Summers", "General"),
            ("2026-06-10", "Placement Drive: Microsoft visiting campus next month", "Placement")
        ]
        cursor.executemany("INSERT INTO notices (date, title, category) VALUES (?, ?, ?)", initial_notices)

    # Clean up legacy test data structural targets
    cursor.execute("DELETE FROM users WHERE email='student@ccet.edu'")

    # Seed User Accounts Matrix
    users_data = [
        ("superadmin@ccet.edu", "superpw", "Super Administrator", None, None, None),
        ("branchadmin@ccet.edu", "branchpw", "Branch Administrator", None, None, None),
        ("faculty@ccet.edu", "facpw", "Faculty", None, None, None),
        ("deptrep@ccet.edu", "deptpw", "Department Representative", None, None, None),
        ("result@ccet.edu", "resultpw", "Result Unit", None, None, None),
        ("exam@ccet.edu", "exampw", "Assistant Examination", None, None, None),
        ("nodal@ccet.edu", "nodalpw", "Nodal Officer", None, None, None),
        ("branchassist@ccet.edu", "assistpw", "Branch Assistant", None, None, None),
        ("clerk@ccet.edu", "clerkpw", "Academic Clerk", None, None, None),
        ("so@ccet.edu", "sopw", "SO", None, None, None),
        ("cse.student@ccet.edu", "studpw", "Student", "Computer Science & Engineering", "2025-2029", "B.E."),
        ("ece.student@ccet.edu", "studpw", "Student", "ECE", "2024-2028", "B.E."),
        ("civil.student@ccet.edu", "studpw", "Student", "Civil", "2023-2027", "B.E."),
        ("mech.student@ccet.edu", "studpw", "Student", "Mech", "2025-2029", "B.E.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (email, password, role, branch, batch, course) VALUES (?, ?, ?, ?, ?, ?)", users_data)

    # Wipe and rebuild static curriculum syllabus assets
    cursor.execute("DELETE FROM syllabus")
    cursor.executescript("""
    -- 1. COMPUTER SCIENCE & ENGINEERING (CSE)
    INSERT INTO syllabus (branch, semester, subject, subject_type, credits) VALUES
    ('Computer Science & Engineering', 1, 'Calculus', 'Theory', 4),
    ('Computer Science & Engineering', 1, 'Quantum Physics', 'Theory', 4),
    ('Computer Science & Engineering', 1, 'Programming Fundamentals', 'Theory', 4),
    ('Computer Science & Engineering', 1, 'Quantum Physics Lab', 'Practical', 1),
    ('Computer Science & Engineering', 1, 'Programming Fundamentals Lab', 'Practical', 1),
    ('Computer Science & Engineering', 2, 'Linear Algebra & Differential Equations', 'Theory', 4),
    ('Computer Science & Engineering', 2, 'Object Oriented Programming', 'Theory', 4),
    ('Computer Science & Engineering', 2, 'Digital Electronics', 'Theory', 4),
    ('Computer Science & Engineering', 2, 'OOP Lab', 'Practical', 2),
    ('Computer Science & Engineering', 3, 'Data Structures & Algorithms', 'Theory', 4),
    ('Computer Science & Engineering', 3, 'Discrete Structures', 'Theory', 4),
    ('Computer Science & Engineering', 3, 'Computer Architecture & Organization', 'Theory', 4),
    ('Computer Science & Engineering', 3, 'Data Structures Lab', 'Practical', 2),
    ('Computer Science & Engineering', 4, 'Operating Systems', 'Theory', 4),
    ('Computer Science & Engineering', 4, 'Database Management Systems', 'Theory', 4),
    ('Computer Science & Engineering', 4, 'Systems Programming', 'Theory', 3),
    ('Computer Science & Engineering', 4, 'DBMS Lab', 'Practical', 2),
    ('Computer Science & Engineering', 5, 'Design & Analysis of Algorithms', 'Theory', 4),
    ('Computer Science & Engineering', 5, 'Computer Networks', 'Theory', 4),
    ('Computer Science & Engineering', 5, 'Formal Language & Automata Theory', 'Theory', 4),
    ('Computer Science & Engineering', 5, 'Computer Networks Lab', 'Practical', 1),
    ('Computer Science & Engineering', 6, 'Software Engineering', 'Theory', 3),
    ('Computer Science & Engineering', 6, 'Compiler Design', 'Theory', 4),
    ('Computer Science & Engineering', 6, 'Artificial Intelligence', 'Theory', 4),
    ('Computer Science & Engineering', 6, 'Data Science Capstone Lab', 'Practical', 2),
    ('Computer Science & Engineering', 7, 'Machine Learning Techniques', 'Theory', 4),
    ('Computer Science & Engineering', 7, 'Cloud Computing Architectures', 'Theory', 4),
    ('Computer Science & Engineering', 7, 'Information Security & Cyber Laws', 'Theory', 3),
    ('Computer Science & Engineering', 7, 'Machine Learning Lab', 'Practical', 2),
    ('Computer Science & Engineering', 8, 'Industrial Project Work', 'Practical', 8),
    ('Computer Science & Engineering', 8, 'Technical Seminar & Viva', 'Theory', 2);

    -- 2. ELECTRONICS & COMMUNICATION ENGINEERING (ECE)
    INSERT INTO syllabus (branch, semester, subject, subject_type, credits) VALUES
    ('ECE', 1, 'Basic Electronics Engineering', 'Theory', 4),
    ('ECE', 1, 'Network Analysis & Synthesis', 'Theory', 4),
    ('ECE', 2, 'Electronic Devices & Circuits', 'Theory', 4),
    ('ECE', 2, 'Signals and Systems', 'Theory', 4),
    ('ECE', 3, 'Digital Electronics Design', 'Theory', 4),
    ('ECE', 3, 'Microprocessors & Microcontrollers', 'Theory', 4),
    ('ECE', 3, 'Digital Infrastructure Lab', 'Practical', 2),
    ('ECE', 4, 'Analog Communication Systems', 'Theory', 4),
    ('ECE', 4, 'Electromagnetic Field Theory', 'Theory', 3),
    ('ECE', 4, 'Hardware Circuit Assembly Lab', 'Practical', 2),
    ('ECE', 5, 'Digital Communication', 'Theory', 4),
    ('ECE', 5, 'Linear Integrated Circuits', 'Theory', 4),
    ('ECE', 5, 'Microcontrollers Architecture Lab', 'Practical', 1),
    ('ECE', 6, 'Digital Signal Processing (DSP)', 'Theory', 4),
    ('ECE', 6, 'VLSI Design Technology', 'Theory', 4),
    ('ECE', 6, 'Advanced VLSI Systems Lab', 'Practical', 2),
    ('ECE', 7, 'Wireless & Cellular Communication', 'Theory', 4),
    ('ECE', 7, 'Optical Fiber Networks', 'Theory', 3),
    ('ECE', 7, 'Microwave Engineering Systems', 'Theory', 3),
    ('ECE', 8, 'Major Capstone Project', 'Practical', 8),
    ('ECE', 8, 'Industry Readiness Viva', 'Theory', 2);

    -- 3. CIVIL ENGINEERING
    INSERT INTO syllabus (branch, semester, subject, subject_type, credits) VALUES
    ('Civil', 1, 'Engineering Mechanics Mechanics', 'Theory', 4),
    ('Civil', 1, 'Surveying Techniques I', 'Theory', 3),
    ('Civil', 2, 'Introduction to Structural Analysis', 'Theory', 4),
    ('Civil', 2, 'Fluid Mechanics Infrastructure', 'Theory', 4),
    ('Civil', 3, 'Advanced Surveying & GIS Mapping', 'Theory', 4),
    ('Civil', 3, 'Concrete Technology & Assays', 'Theory', 3),
    ('Civil', 3, 'Surveying Lab Field Work', 'Practical', 2),
    ('Civil', 4, 'Design of Concrete Structures', 'Theory', 4),
    ('Civil', 4, 'Geotechnical Engineering Foundations', 'Theory', 4),
    ('Civil', 4, 'Soil Mechanics Testing Lab', 'Practical', 2),
    ('Civil', 5, 'Design of Steel Structures', 'Theory', 4),
    ('Civil', 5, 'Transportation & Highway Engineering', 'Theory', 4),
    ('Civil', 5, 'Hydraulics Modeling Lab', 'Practical', 1),
    ('Civil', 6, 'Environmental Engineering Matrices', 'Theory', 4),
    ('Civil', 6, 'Water Resources Planning', 'Theory', 3),
    ('Civil', 6, 'Structural Design Studio', 'Practical', 2),
    ('Civil', 7, 'Construction Management & Planning', 'Theory', 3),
    ('Civil', 7, 'Bridge & Tunnel Engineering', 'Theory', 4),
    ('Civil', 7, 'Earthquake Resistant Structures', 'Theory', 3),
    ('Civil', 8, 'Civil Engineering Thesis Project', 'Practical', 8),
    ('Civil', 8, 'Comprehensive Field Viva', 'Theory', 2);

    -- 4. MECHANICAL ENGINEERING (MECH)
    INSERT INTO syllabus (branch, semester, subject, subject_type, credits) VALUES
    ('Mech', 1, 'Engineering Graphics & Draft', 'Theory', 3),
    ('Mech', 1, 'Thermodynamics Fundamentals', 'Theory', 4),
    ('Mech', 2, 'Applied Mechanics Systems', 'Theory', 4),
    ('Mech', 2, 'Material Science Processing', 'Theory', 4),
    ('Mech', 3, 'Kinematics of Machinery', 'Theory', 4),
    ('Mech', 3, 'Strength of Engineering Materials', 'Theory', 4),
    ('Mech', 3, 'Machine Shop Practice I', 'Practical', 2),
    ('Mech', 4, 'Fluid Mechanics & Machinery', 'Theory', 4),
    ('Mech', 4, 'Manufacturing Technology', 'Theory', 3),
    ('Mech', 4, 'Fluid Power Systems Lab', 'Practical', 2),
    ('Mech', 5, 'Dynamics of Machinery Systems', 'Theory', 4),
    ('Mech', 5, 'Heat and Mass Transfer', 'Theory', 4),
    ('Mech', 5, 'Thermal Engineering Lab', 'Practical', 1),
    ('Mech', 6, 'Machine Design Elements', 'Theory', 4),
    ('Mech', 6, 'Internal Combustion Engines', 'Theory', 3),
    ('Mech', 6, 'Metrology & Instrumentation Lab', 'Practical', 2),
    ('Mech', 7, 'CAD/CAM Computer Integration', 'Theory', 4),
    ('Mech', 7, 'Refrigeration & Air Conditioning', 'Theory', 3),
    ('Mech', 7, 'Robotics & Automation Systems', 'Theory', 3),
    ('Mech', 8, 'Mechanical Capstone Project', 'Practical', 8),
    ('Mech', 8, 'Technical Defense Viva', 'Theory', 2);
    """)

    # Seed cross-platform historical grade metrics
    cursor.executescript("""
    INSERT OR IGNORE INTO students (roll_no, name, branch, semester, session) VALUES
    ('CSE101','CSE Student Sem1','CSE',1,'2024-2028'),
    ('CSE201','CSE Student Sem2','CSE',2,'2024-2028'),
    ('CSE301','CSE Student Sem3','CSE',3,'2024-2028'),
    ('CSE401','CSE Student Sem4','CSE',4,'2024-2028'),
    ('CSE501','CSE Student Sem5','CSE',5,'2024-2028'),
    ('CSE601','CSE Student Sem6','CSE',6,'2024-2028'),
    ('CSE701','CSE Student Sem7','CSE',7,'2024-2028'),
    ('CSE801','CSE Student Sem8','CSE',8,'2024-2028'),
    ('ECE101','ECE Student Sem1','ECE',1,'2024-2028'),
    ('ECE201','ECE Student Sem2','ECE',2,'2024-2028'),
    ('ECE301','ECE Student Sem3','ECE',3,'2024-2028'),
    ('ECE401','ECE Student Sem4','ECE',4,'2024-2028'),
    ('ECE501','ECE Student Sem5','ECE',5,'2024-2028'),
    ('ECE601','ECE Student Sem6','ECE',6,'2024-2028'),
    ('ECE701','ECE Student Sem7','ECE',7,'2024-2028'),
    ('ECE801','ECE Student Sem8','ECE',8,'2024-2028'),
    ('CIV101','Civil Student Sem1','Civil',1,'2024-2028'),
    ('CIV201','Civil Student Sem2','Civil',2,'2024-2028'),
    ('CIV301','Civil Student Sem3','Civil',3,'2024-2028'),
    ('CIV401','Civil Student Sem4','Civil',4,'2024-2028'),
    ('CIV501','Civil Student Sem5','Civil',5,'2024-2028'),
    ('CIV601','Civil Student Sem6','Civil',6,'2024-2028'),
    ('CIV701','Civil Student Sem7','Civil',7,'2024-2028'),
    ('CIV801','Civil Student Sem8','Civil',8,'2024-2028'),
    ('MEC101','Mech Student Sem1','Mech',1,'2024-2028'),
    ('MEC201','Mech Student Sem2','Mech',2,'2024-2028'),
    ('MEC301','Mech Student Sem3','Mech',3,'2024-2028'),
    ('MEC401','Mech Student Sem4','Mech',4,'2024-2028'),
    ('MEC501','Mech Student Sem5','Mech',5,'2024-2028'),
    ('MEC601','Mech Student Sem6','Mech',6,'2024-2028'),
    ('MEC701','Mech Student Sem7','Mech',7,'2024-2028'),
    ('MEC801','Mech Student Sem8','Mech',8,'2024-2028');

    INSERT OR IGNORE INTO marks (roll_no, subject, marks, grade) VALUES
    ('CSE101','Math',80,'A'),('CSE101','Physics',75,'B+'),
    ('CSE201','Math',85,'A'),('CSE201','CSE101',90,'A+'),
    ('CSE301','DSA',78,'B+'),('CSE301','OS',82,'A'),
    ('CSE401','DBMS',88,'A'),('CSE401','Networks',76,'B+'),
    ('CSE501','AI',91,'A+'),('CSE501','ML',89,'A'),
    ('CSE601','Compiler',84,'A'),('CSE601','Cloud',80,'A'),
    ('CSE701','Big Data',77,'B+'),('CSE701','IoT',83,'A'),
    ('CSE801','Project',92,'A+'),('CSE801','Seminar',88,'A'),
    ('ECE101','Math',70,'B'),('ECE101','Electronics',74,'B+'),
    ('ECE201','Circuits',82,'A'),('ECE201','Signals',79,'B+'),
    ('ECE301','Digital',85,'A'),('ECE301','Microprocessors',80,'A'),
    ('ECE401','Communication',78,'B+'),('ECE401','VLSI',83,'A'),
    ('ECE501','Embedded',86,'A'),('ECE501','Control',82,'A'),
    ('ECE601','DSP',88,'A'),('ECE601','Wireless',84,'A'),
    ('ECE701','Optical',76,'B+'),('ECE701','Nanoelectronics',80,'A'),
    ('ECE801','Project',90,'A+'),('ECE801','Seminar',85,'A'),
    ('CIV101','Math',68,'B'),('CIV101','Mechanics',72,'B+'),
    ('CIV201','Structures',80,'A'),('CIV201','Surveying',78,'B+'),
    ('CIV301','Hydraulics',82,'A'),('CIV301','Concrete',79,'B+'),
    ('CIV401','Steel Design',85,'A'),('CIV401','Geotech',81,'A'),
    ('CIV501','Transportation',77,'B+'),('CIV501','Water Resources',83,'A'),
    ('CIV601','Construction',84,'A'),('CIV601','Environment',80,'A'),
    ('CIV701','Urban Planning',86,'A'),('CIV701','Bridge Design',82,'A'),
    ('CIV801','Project',91,'A+'),('CIV801','Seminar',87,'A'),
    ('MEC101','Math',72,'B+'),('MEC101','Mechanics',74,'B+'),
    ('MEC201','Thermo',80,'A'),('MEC201','Materials',78,'B+'),
    ('MEC301','Dynamics',82,'A'),('MEC301','Manufacturing',79,'B+'),
    ('MEC401','Design',85,'A'),('MEC401','Fluid Mechanics',81,'A'),
    ('MEC501','Heat Transfer',77,'B+'),('MEC501','Robotics',83,'A'),
    ('MEC601','CAD/CAM',84,'A'),('MEC601','Automation',80,'A'),
    ('MEC701','Energy Systems',86,'A'),('MEC701','Mechatronics',82,'A'),
    ('MEC801','Project',91,'A+'),('MEC801','Seminar',87,'A');
    """)

    # Commit all changes and close safely at the very end
    conn.commit()
    conn.close()
    print("🎉 SUCCESS: Database architecture built and populated with zero errors!")

if __name__ == "__main__":
    setup_database()