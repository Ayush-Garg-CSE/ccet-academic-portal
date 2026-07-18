# e-Akadamik Portal (CCET Replica)

A full-stack replica of the **Chandigarh College of Engineering and Technology (CCET) e-Akadamik website**. Built using Python, Flask, and SQLite3, this portal simulates a unified academic management environment.

> 📌 **Project Status**: Development is concluded at **Milestone 1 (Student Section)**. The student dashboard, result parser, and profile utilities are fully functional. Other sections display error placeholders but have complete frontend designs.

---

## 🚀 Quick Start (Local Setup)

Run the following commands in your terminal to launch the portal:

```bash
# Clone the repository
git clone https://github.com/Ayush-Garg-CSE/ccet-academic-portal.git

# Install dependencies
pip install flask

# Run the application
python app.py
👉 Open your browser and navigate to: http://127.0.0.1:5000

🔑 Pre-Configured Test Accounts
Log in directly using these pre-loaded student roles to test different branch layouts:

CSE: cse.student@ccet.ac.in | Password: studpw

Mechanical: mech.student@ccet.ac.in | Password: studpw

ECE: ece.student@ccet.ac.in | Password: studpw

Civil: civil.student@ccet.ac.in | Password: studpw

🛠️ Feature Breakdown
🟢 Fully Functional Features
Authentication & Security: Dynamic login states, working Forgot Password flows, a functional Settings tab to change passwords, and a clean Logout mechanism.

Examination: Allows students to fill out exam registration entries. Administrators can view and verify all active submissions here:

🔗 http://127.0.0.1:5000/admin/verify-submissions

Result Portal: Dynamic semester marks display. For even semesters, it automatically calculates and updates the Yearly CGPA using historical database records. Includes robust state-driven error handles if results are missing. Admin upload link:

🔗 http://127.0.0.1:5000/upload_results

Admin Notice Engine: Inject real-time announcements onto the portal via:

🔗 http://127.0.0.1:5000/admin/add-notice

🟡 Structural / Prototype Features
Attendance: Purely a visual prototype. The interface looks exact and high-fidelity, but backend logic is unmapped.

*   **Syllabus & DocUpload:** Fully operational. They actively query the database to retrieve, map, and display the official syllabus datasets and user e-documents dynamically on the frontend.

*   **Settings & Security:** Fully functional. Students can actively change their account passwords directly inside the active session settings panel.

*   **Forgot Password:** A working authentication recovery flow accessible from the login home screen, allowing users to securely reset account credentials.

*   **Logout:** Standardized token and session clearance routing works completely, securely wiping user states upon exit.

Built with Flask, SQLite3, HTML5, and CSS3.
