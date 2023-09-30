import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import sqlite3
import datetime
import base64
# import io

# Initialize the 'name' variable globally
name = ''

# Function to create a database connection
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('student_info.db')
    except sqlite3.Error as e:
        st.error(f"Error creating database connection: {e}")
    return conn

# Function to create the database table
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_info (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                branch TEXT NOT NULL,
                roll_number TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")

# Function to check if a user can enter data after 20 hours
def can_enter_data(conn, name, branch, roll_number):
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp FROM student_info WHERE name = ? AND branch = ? AND roll_number = ? ORDER BY timestamp DESC LIMIT 1",
                   (name, branch, roll_number))
    last_entry = cursor.fetchone()
    if last_entry:
        last_entry_time = datetime.datetime.strptime(last_entry[0], "%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        time_difference = current_time - last_entry_time
        return time_difference.total_seconds() >= 30  # 20 hours in seconds
    else:
        return True  # No previous entry found, can enter data

# Function to generate QR code as a base64 encoded image with a name
def generate_qr_code_with_name(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Create a higher-resolution PIL image
    img_with_name = Image.new('RGB', (qr_img.size[0] * 3, qr_img.size[1] * 3), "white")
    img_with_name.paste(qr_img.resize(img_with_name.size), (0, 0))

    # Draw the name text on the image with improved quality
    draw = ImageDraw.Draw(img_with_name)
    font = ImageFont.truetype("arial.ttf", 60)  # Use a higher quality font and size
    text = f"Name: {name}"
    text_width, text_height = draw.textsize(text, font=font)
    draw.text(((img_with_name.size[0] - text_width) // 2, img_with_name.size[1] - text_height - 10), text, fill="black", font=font)

    return img_with_name

# Streamlit app
def main():
    global name  # Use the global 'name' variable
    # st.title("Student Information App")

    # Sidebar navigation
    page = st.sidebar.selectbox("Select a page", ["QR Code Generator", "Database"])

    if page == "QR Code Generator":
        st.title("QR Code Generator")
        # Input fields for name, branch/division, and roll number
        name = st.text_input("Enter Name:")
        branch_division = st.text_input("Enter Branch/Division:")
        roll_number = st.text_input("Enter Roll Number:")

        # Button to generate QR code
        if st.button("Generate QR Code"):
            if name and branch_division and roll_number:
                data = f"Name: {name}\nBranch/Division: {branch_division}\nRoll Number: {roll_number}"
                qr_code_with_name = generate_qr_code_with_name(data)

                # Display the QR code with name at the top with improved quality
                st.image(qr_code_with_name, use_column_width=True, caption=f"QR Code for {name}")

    elif page == "Database":
        st.title("Database")
        conn = create_connection()
        if conn is not None:
            create_table(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student_info")
            data = cursor.fetchall()
            st.write("Database Contents:")
            for row in data:
                st.write(row)

            if st.button("Download All Data"):
                df = pd.DataFrame(data, columns=["ID", "Name", "Branch", "Roll Number", "Timestamp"])
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                st.markdown(f'<a href="data:file/csv;base64,{b64}" download="student_data.csv">Download All Data</a>',
                            unsafe_allow_html=True)

        # Add a button to clean (delete) the database with two-step verification
        if st.button("Clean Database"):
            if conn is not None:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM student_info")
                conn.commit()
                st.success("All data in the database has been deleted!")

if __name__ == '__main__':
    main()
