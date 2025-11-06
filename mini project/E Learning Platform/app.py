import sqlite3
import json
from flask import Flask, jsonify, redirect, request # Added 'request'
from flask_cors import CORS 

# --- FLASK APP SETUP ---
app = Flask(__name__)
CORS(app) 

DATABASE = 'e_learning.db'

def get_db_connection():
    """Connects to the SQLite database and sets up row factory for dict-like rows."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and populates it with dummy data."""
    print("Initializing database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (DBMS Entity)
    # Role 'I' for Instructor, 'S' for Student
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
        );
    """)

    # 2. Courses Table (DBMS Entity)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Courses (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            instructor_id INTEGER,
            FOREIGN KEY (instructor_id) REFERENCES Users(id)
        );
    """)

    # 3. Lessons Table (DBMS Entity) - Strong relationship with Courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Lessons (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (course_id) REFERENCES Courses(id)
        );
    """)

    # 4. Enrollments Table (DBMS Relationship)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Enrollments (
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enroll_date DATE DEFAULT CURRENT_DATE,
            PRIMARY KEY (user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES Users(id),
            FOREIGN KEY (course_id) REFERENCES Courses(id)
        );
    """)

    # --- Sample Data Insertion ---
    
    # Insert Users (Added student user ID 4 for enrollment testing)
    cursor.execute("INSERT OR IGNORE INTO Users (id, name, email, role) VALUES (?, ?, ?, ?)", (1, 'Dr. Aris Patel', 'aris@plat.edu', 'I'))
    cursor.execute("INSERT OR IGNORE INTO Users (id, name, email, role) VALUES (?, ?, ?, ?)", (2, 'Prof. Lin Wang', 'lin@plat.edu', 'I'))
    cursor.execute("INSERT OR IGNORE INTO Users (id, name, email, role) VALUES (?, ?, ?, ?)", (3, 'Dr. Anya Sharma', 'anya@plat.edu', 'I'))
    cursor.execute("INSERT OR IGNORE INTO Users (id, name, email, role) VALUES (?, ?, ?, ?)", (4, 'Mock Student User', 'student@plat.edu', 'S'))
    
    # Insert Courses 
    cursor.execute("INSERT OR IGNORE INTO Courses (id, title, description, instructor_id) VALUES (?, ?, ?, ?)", 
                   (101, 'Introduction to SQL and Relational Databases', 'Learn the fundamental concepts of database management, normalization, and SQL querying.', 1))
    cursor.execute("INSERT OR IGNORE INTO Courses (id, title, description, instructor_id) VALUES (?, ?, ?, ?)", 
                   (102, 'Python Web Development with Flask', 'A practical guide to building REST APIs using the Flask framework.', 2))
    cursor.execute("INSERT OR IGNORE INTO Courses (id, title, description, instructor_id) VALUES (?, ?, ?, ?)", 
                   (103, 'Data Structures & Algorithms in Python', 'Master core DSA concepts including trees, graphs, and dynamic programming for coding interviews.', 1))
    cursor.execute("INSERT OR IGNORE INTO Courses (id, title, description, instructor_id) VALUES (?, ?, ?, ?)", 
                   (104, 'Advanced Cloud Computing (AWS Focus)', 'Explore serverless architecture, microservices, and large-scale deployment using AWS.', 3))

    # Insert Lessons 
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (101, 'What is a Database?', 'A database is an organized collection of data...'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (101, 'SQL Basic Queries', 'SELECT, FROM, and WHERE clauses are the foundation of SQL.'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (102, 'Setting up the Flask Project', 'Initialize your Python environment and install Flask.'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (102, 'Creating API Endpoints', 'Define routes to handle GET and POST requests.'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (103, 'Big O Notation and Time Complexity', 'Understanding how to measure algorithm efficiency.'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (103, 'Introduction to Binary Search Trees', 'Balanced vs. unbalanced trees and common operations.'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (104, 'Serverless Functions (Lambda)', 'Building and deploying FaaS functions.'))
    cursor.execute("INSERT OR IGNORE INTO Lessons (course_id, title, content) VALUES (?, ?, ?)", (104, 'Containerization with Docker and ECS', 'Packaging applications for scalable cloud deployment.'))


    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# Initialize database when the app starts
init_db()


# --- API ENDPOINTS ---

@app.route('/', methods=['GET'])
def index_redirect():
    """Redirects the root URL to the courses API endpoint."""
    return redirect('/api/courses') 

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """API endpoint to fetch a list of all courses."""
    conn = get_db_connection()
    conn.row_factory = dict_factory
    courses = conn.execute("""
        SELECT 
            C.id, C.title, C.description, U.name AS instructor_name
        FROM 
            Courses C
        JOIN 
            Users U ON C.instructor_id = U.id
    """).fetchall()
    conn.close()
    
    course_list = [dict(row) for row in courses]
    return jsonify(course_list)

@app.route('/api/course/<int:course_id>', methods=['GET'])
def get_course_detail(course_id):
    """
    API endpoint to fetch detailed course information, its lessons, 
    and check enrollment status for a given user.
    """
    conn = get_db_connection()
    conn.row_factory = dict_factory
    
    # Get user_id from query parameters (used by frontend to check status)
    user_id = request.args.get('user_id', type=int)
    
    # Fetch Course Details
    course = conn.execute("""
        SELECT 
            C.id, C.title, C.description, U.name AS instructor_name
        FROM 
            Courses C
        JOIN 
            Users U ON C.instructor_id = U.id
        WHERE C.id = ?
    """, (course_id,)).fetchone()

    if course is None:
        conn.close()
        return jsonify({"error": "Course not found"}), 404
        
    # Check Enrollment Status (DBMS Query)
    is_enrolled = False
    if user_id:
        enrollment = conn.execute("""
            SELECT 1 FROM Enrollments
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_id)).fetchone()
        if enrollment:
            is_enrolled = True
        
    # Fetch Lessons for the Course
    lessons = conn.execute("""
        SELECT id, title, content 
        FROM Lessons 
        WHERE course_id = ? 
        ORDER BY id
    """, (course_id,)).fetchall()
    
    conn.close()
    
    course_data = dict(course)
    course_data['lessons'] = [dict(row) for row in lessons]
    course_data['is_enrolled'] = is_enrolled # Add enrollment status to response

    return jsonify(course_data)

@app.route('/api/enroll', methods=['POST'])
def enroll_user():
    """API endpoint to handle user enrollment into a course (the 'buy' action)."""
    data = request.get_json()
    user_id = data.get('user_id')
    course_id = data.get('course_id')
    
    if not all([user_id, course_id]):
        return jsonify({"error": "Missing user_id or course_id"}), 400

    conn = get_db_connection()
    try:
        # Check if already enrolled
        check = conn.execute("SELECT 1 FROM Enrollments WHERE user_id = ? AND course_id = ?", (user_id, course_id)).fetchone()
        if check:
            conn.close()
            return jsonify({"message": "Already enrolled"}), 200

        # Perform the Enrollment (DBMS Insert)
        conn.execute("INSERT INTO Enrollments (user_id, course_id) VALUES (?, ?)", (user_id, course_id))
        conn.commit()
        return jsonify({"message": "Enrollment successful!"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Enrollment failed due to database constraint"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)