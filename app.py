from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import os
import firebase_admin
from firebase_admin import credentials, db
import json

from dotenv import load_dotenv
load_dotenv()

# Load Firebase credentials from .env file
firebase_cred = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))
google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')


# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_cred)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://employee-management-syst-cdbed-default-rtdb.firebaseio.com/'  # Replace with your Firebase Realtime Database URL
})

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random key

# Mock admin credentials (you can replace these with a database in the future)
admin_username = 'admin'
admin_password = generate_password_hash('admin')  # Hashed password

@app.route('/')
def home():
    return render_template('admin.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error_message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials
        if username == admin_username and check_password_hash(admin_password, password):
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            error_message = 'Invalid username or password.'

    return render_template('admin.html', error_message=error_message)

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    return render_template('dashboard.html')

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        employee_email = request.form['email']
        employee_name = request.form['name']
        employee_phone = request.form['phone']
        employee_code = request.form['employeecode']
        employee_unit = request.form['employeeunit']
        employee_latitude = request.form['latitude']
        employee_longitude = request.form['longitude']

        
        new_employee = {
            'email': employee_email,
            'name': employee_name,
            'phone': employee_phone,
            'employee_code': employee_code,
            'employee_unit': employee_unit,
            'employee_latitude': employee_latitude,
            'employee_longitude': employee_longitude
        }

        try:
            ref = db.reference(f'/employees/{employee_email.split("@")[0]}')
            existing_employee = ref.get()  # Check if employee already exists

            if existing_employee:
                flash('Employee with this number already exists!', 'warning')
            else:
                ref.set(new_employee)
                flash('Employee added successfully!', 'success')
            
        except Exception as e:
            flash('Failed to add employee!', 'danger')

    return render_template('add_employee.html')



@app.route('/view_employee')
def view_employee():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    # Get all employee data from Firebase Realtime Database
    ref = db.reference('employees')
    employees = ref.get()  # Get all employee records
    
    # Pass employee data to the template
    return render_template('view_employee.html', employees=employees)

@app.route('/delete_employee/<email>', methods=['POST'])
def delete_employee(email):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    try:
        ref = db.reference(f'/employees/{email}')
        if ref.get():
            ref.delete()
            flash('Employee deleted successfully!', 'success')
        else:
            flash('Employee not found!', 'warning')
    except Exception as e:
        flash('Failed to delete employee!', 'danger')

    return redirect(url_for('view_employee'))

@app.route('/view_location/<latitude>/<longitude>')
def view_location(latitude, longitude):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    return render_template('view_location.html', latitude=latitude, longitude=longitude, api_key=google_maps_api_key)

@app.route('/edit_employee/<email>', methods=['GET', 'POST'])
def edit_employee(email):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    ref = db.reference(f'/employees/{email}')
    employee = ref.get()

    if not employee:
        flash('Employee not found!', 'warning')
        return redirect(url_for('view_employee'))

    if request.method == 'POST':
        # Get updated details from the form
        updated_employee = {
            'email': request.form['email'],
            'name': request.form['name'],
            'phone': request.form['phone'],
            'employee_code': request.form['employeecode'],
            'employee_unit': request.form['employeeunit'],
            'employee_latitude': request.form['latitude'],
            'employee_longitude': request.form['longitude']
        }

        try:
            # Update the employee details in Firebase
            ref.set(updated_employee)
            flash('Employee details updated successfully!', 'success')
        except Exception as e:
            flash('Failed to update employee!', 'danger')

        return redirect(url_for('view_employee'))

    return render_template('edit_employee.html', employee=employee, phone=phone)

@app.route('/view_all_locations')
def view_all_locations():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    # Get all employee data from Firebase
    ref = db.reference('employees')
    employees = ref.get()

    # Pass employee data to the template
    return render_template('view_all_locations.html', employees=employees, api_key=google_maps_api_key)



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)