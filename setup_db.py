import sqlite3

# connect to database (creates file if not exists)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# create table for users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# insert sample data with all roles (safe insert)
users_data = [
    ("superadmin@ccet.edu", "superpw", "Super Administrator"),
    ("branchadmin@ccet.edu", "branchpw", "Branch Administrator"),
    ("faculty@ccet.edu", "facpw", "Faculty"),
    ("deptrep@ccet.edu", "deptpw", "Department Representative"),
    ("result@ccet.edu", "resultpw", "Result Unit"),
    ("student@ccet.edu", "studpw", "Student"),
    ("exam@ccet.edu", "exampw", "Assistant Examination"),
    ("nodal@ccet.edu", "nodalpw", "Nodal Officer"),
    ("branchassist@ccet.edu", "assistpw", "Branch Assistant"),
    ("clerk@ccet.edu", "clerkpw", "Academic Clerk"),
    ("so@ccet.edu", "sopw", "SO")
]
cursor.executemany("INSERT OR IGNORE INTO users (email, password, role) VALUES (?, ?, ?)", users_data)

# ✅ new table for subject assignments
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

# ✅ new table for students
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL,
    name TEXT NOT NULL,
    branch TEXT NOT NULL,
    semester INTEGER NOT NULL,
    session TEXT NOT NULL
)
""")

# ✅ new table for marks
cursor.execute("""
CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL,
    subject TEXT NOT NULL,
    marks INTEGER NOT NULL,
    grade TEXT NOT NULL
)
""")

# ✅ new table for attendance
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

# ✅ new table for messages (persistent stacking)
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    category TEXT NOT NULL
)
""")

# ✅ new table for syllabus
cursor.execute("""
CREATE TABLE IF NOT EXISTS syllabus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch TEXT NOT NULL,
    semester INTEGER NOT NULL,
    subject TEXT NOT NULL
)
""")

# ✅ Insert 32 students + marks
cursor.executescript("""
-- Insert 32 students (4 branches × 8 semesters)
INSERT INTO students (roll_no, name, branch, semester, session) VALUES
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

-- Insert marks (2 subjects per student for demo)
INSERT INTO marks (roll_no, subject, marks, grade) VALUES
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

# ✅ Insert fictional syllabus subjects for all branches
cursor.executescript("""
INSERT INTO syllabus (branch, semester, subject) VALUES
-- Mechanical Engineering
('Mechanical', 1, 'Engineering Mathematics I'),
('Mechanical', 1, 'Engineering Physics'),
('Mechanical', 2, 'Engineering Mechanics'),
('Mechanical', 2, 'Engineering Mathematics II'),
('Mechanical', 3, 'Thermodynamics'),
('Mechanical', 3, 'Strength of Materials'),
('Mechanical', 4, 'Fluid Mechanics'),
('Mechanical', 4, 'Manufacturing Processes'),
('Mechanical', 5, 'Dynamics of Machinery'),
('Mechanical', 5, 'Heat Transfer'),
('Mechanical', 6, 'Machine Design'),
('Mechanical', 6, 'Control Systems'),
('Mechanical', 7, 'Robotics'),
('Mechanical', 7, 'Energy Systems'),
('Mechanical', 8, 'Project Work'),
('Mechanical', 8, 'Seminar'),

-- Computer Science Engineering
('CSE', 1, 'Programming in C'),
('CSE', 1, 'Discrete Mathematics'),
('CSE', 2, 'Data Structures'),
('CSE', 2, 'Computer Organization'),
('CSE', 3, 'Algorithms'),
('CSE', 3, 'Operating Systems'),
('CSE', 4, 'Database Management Systems'),
('CSE', 4, 'Computer Networks'),
('CSE', 5, 'Artificial Intelligence'),
('CSE', 5, 'Machine Learning'),
('CSE', 6, 'Compiler Design'),
('CSE', 6, 'Cloud Computing'),
('CSE', 7, 'Big Data Analytics'),
('CSE', 7, 'Internet of Things'),
('CSE', 8, 'Major Project'),
('CSE', 8, 'Seminar'),

-- Electronics & Communication Engineering
('ECE', 1, 'Basic Electronics'),
('ECE', 1, 'Engineering Mathematics I'),
('ECE', 2, 'Circuit Theory'),
('ECE', 2, 'Signals and Systems'),
('ECE', 3, 'Digital Electronics'),
('ECE', 3, 'Microprocessors'),
('ECE', 4, 'Communication Systems'),
('ECE', 4, 'VLSI Design'),
('ECE', 5, 'Embedded Systems'),
('ECE', 5, 'Control Engineering'),
('ECE', 6, 'Digital Signal Processing'),
('ECE', 6, 'Wireless Communication'),
('ECE', 7, 'Optical Communication'),
('ECE', 7, 'Nanoelectronics'),
('ECE', 8, 'Project Work'),
('ECE', 8, 'Seminar'),

-- Civil Engineering
('Civil', 1, 'Engineering Mathematics I'),
('Civil', 1, 'Engineering Mechanics'),
('Civil', 2, 'Structural Analysis'),
('Civil', 2, 'Surveying'),
('Civil', 3, 'Hydraulics'),
('Civil', 3, 'Concrete Technology'),
('Civil', 4, 'Steel Design'),
('Civil', 4, 'Geotechnical Engineering'),
('Civil', 5, 'Transportation Engineering'),
('Civil', 5, 'Water Resources Engineering'),
('Civil', 6, 'Construction Management'),
('Civil', 6, 'Environmental Engineering'),
('Civil', 7, 'Urban Planning'),
('Civil', 7, 'Bridge Design'),
('Civil', 8, 'Project Work'),
('Civil', 8, 'Seminar');
""")

conn.commit()
conn.close()

print("Database setup complete with all roles, assigned_subjects table, students table, marks table, attendance table, messages table, and syllabus table populated!")




