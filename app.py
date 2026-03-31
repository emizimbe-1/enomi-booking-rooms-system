
import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
password TEXT,
role TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS rooms (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
capacity INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS bookings (
id INTEGER PRIMARY KEY AUTOINCREMENT,
room TEXT,
date TEXT,
time TEXT,
user TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS timetable (
id INTEGER PRIMARY KEY AUTOINCREMENT,
room TEXT,
date TEXT,
time TEXT,
status TEXT)''')

conn.commit()

# Seed admin
c.execute("SELECT * FROM users WHERE email='admin@enomi.com'")
if not c.fetchone():
    c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
              ("Admin","admin@enomi.com","admin","admin"))
    conn.commit()

# Auth
if "user" not in st.session_state:
    st.session_state.user = None

def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
        user = c.fetchone()
        if user:
            st.session_state.user = user
        else:
            st.error("Invalid credentials")

def register():
    st.title("Register")
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                  (name,email,password,"rep"))
        conn.commit()
        st.success("Registered! Now login.")

if not st.session_state.user:
    choice = st.selectbox("Select", ["Login","Register"])
    if choice == "Login":
        login()
    else:
        register()
    st.stop()

st.sidebar.write(f"Logged in as: {st.session_state.user[1]}")

menu = ["Dashboard","Rooms","Book","Upload Timetable","Cancel Lecture"]
choice = st.sidebar.selectbox("Menu", menu)

def get_rooms():
    c.execute("SELECT name FROM rooms")
    return [r[0] for r in c.fetchall()]

def is_busy(room,date,time):
    c.execute("SELECT * FROM timetable WHERE room=? AND date=? AND time=? AND status='active'",(room,date,time))
    return c.fetchone()

def is_booked(room,date,time):
    c.execute("SELECT * FROM bookings WHERE room=? AND date=? AND time=?",(room,date,time))
    return c.fetchone()

if choice == "Dashboard":
    st.title("Dashboard")
    st.write("System overview")

elif choice == "Rooms":
    st.subheader("Manage Rooms")
    room = st.text_input("Room Name")
    cap = st.number_input("Capacity",0)
    if st.button("Add Room"):
        c.execute("INSERT INTO rooms (name,capacity) VALUES (?,?)",(room,cap))
        conn.commit()
        st.success("Room added")

    st.write(get_rooms())

elif choice == "Book":
    st.subheader("Book Room")
    room = st.selectbox("Room", get_rooms())
    date = st.date_input("Date")
    time = st.time_input("Time")

    if st.button("Book"):
        if is_busy(room,str(date),str(time)):
            st.error("Busy")
        elif is_booked(room,str(date),str(time)):
            st.error("Already booked")
        else:
            c.execute("INSERT INTO bookings (room,date,time,user) VALUES (?,?,?,?)",
                      (room,str(date),str(time),st.session_state.user[1]))
            conn.commit()
            st.success("Booked!")

elif choice == "Upload Timetable":
    st.subheader("Upload CSV")
    file = st.file_uploader("Upload timetable CSV")

    if file:
        df = pd.read_csv(file)
        for _,row in df.iterrows():
            c.execute("INSERT INTO timetable (room,date,time,status) VALUES (?,?,?,?)",
                      (row['room'],row['date'],row['time'],"active"))
        conn.commit()
        st.success("Uploaded!")

elif choice == "Cancel Lecture":
    st.subheader("Cancel")
    c.execute("SELECT id,room,date,time FROM timetable WHERE status='active'")
    data = c.fetchall()
    for d in data:
        if st.button(f"Cancel {d[1]} {d[2]} {d[3]}"):
            c.execute("UPDATE timetable SET status='cancelled' WHERE id=?", (d[0],))
            conn.commit()
            st.success("Cancelled")
