from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import os
import firebase_admin
from firebase_admin import credentials, db
import json

from dotenv import load_dotenv
load_dotenv()
from datetime import datetime

import re

isDevelopment = False

def verify_email(email: str) -> str:
    match = re.match(r"([^@]+)@(.+)", email)
    if not match:
        raise ValueError("Invalid email format")
    
    local_part, domain = match.groups()
    if '.' in local_part:
        local_part = local_part.replace('.', '_dot_')
    
    return f"{local_part}@{domain}"

def revert_email(email: str) -> str:
    match = re.match(r"([^@]+)@(.+)", email)
    if not match:
        raise ValueError("Invalid email format")
    
    local_part, domain = match.groups()
    if '_dot_' in local_part:
        local_part = local_part.replace('_dot_', '.')
    
    return f"{local_part}@{domain}"

# Load Firebase credentials from .env file


if isDevelopment:
    print("In Development")
    firebase_cred = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))
    if not firebase_cred:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY not set!")
    cred = credentials.Certificate(firebase_cred)
else:
    print("In Production")
    firebase_cred = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    if not firebase_cred:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY not set!")
    cred = credentials.Certificate(json.loads(firebase_cred))

google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize Firebase Admin SDK
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://employee-tracking-system-ea638-default-rtdb.firebaseio.com'  # Replace with your Firebase Realtime Database URL
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

    unit_ref = db.reference('units')
    units = unit_ref.get() or {}

    categories_ref = db.reference('categories')
    categories = categories_ref.get() or {}

    if request.method == 'POST':
        employee_email = request.form['email']
        employee_name = request.form['name']
        employee_phone = request.form['phone']
        category = request.form['category']
        employee_code = request.form['employeecode']
        employee_unit = request.form['employeeunit']
        # employee_latitude = request.form['latitude']
        # employee_longitude = request.form['longitude']

        
        new_employee = {
            'email': employee_email.lower(),
            'name': employee_name,
            'phone': employee_phone,
            'category': category,
            'employee_code': employee_code,
            'employee_unit': employee_unit,
            'employee_latitude': "",
            'employee_longitude': ""
        }

        employee_email = verify_email(employee_email)

        print(employee_email)

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

    return render_template('add_employee.html', units=units, categories=categories)

@app.route('/view_employee')
def view_employee():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    # Get all employee data from Firebase Realtime Database
    ref = db.reference('employees')
    employees = ref.get()  # Get all employee records

    print(employees)
    
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

    return render_template('edit_employee.html', employee=employee, email=email)

@app.route('/view_all_locations')
def view_all_locations():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    # Get all employee data from Firebase
    ref = db.reference('employees')
    employees = ref.get()

    # Pass employee data to the template
    return render_template('view_all_locations.html', employees=employees, api_key=google_maps_api_key)

@app.route('/location_history/<string:email>')
def location_history(email):
    # Reference to the employee's location tracking data in Firebase
    employee_ref = db.reference(f'employees/{email}/location_tracking')
    location_history = employee_ref.get()
    # Convert nested data (date -> time -> coordinates) to a list for easier rendering
    history_data = []
    if location_history:
        for date, times in location_history.items():
            for time, coords in times.items():
                record = {
                    'date': date,
                    'time': time,
                    'latitude': coords.get('latitude'),
                    'longitude': coords.get('longitude')
                }
                history_data.append(record)

    # Sort history data by date and time
    history_data.sort(key=lambda x: (x['date'], x['time']))

    return render_template('location_history.html', history=history_data, email=email, api_key=google_maps_api_key)

@app.route('/location_map')
def location_map():
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    return render_template("location_map.html", latitude=latitude, longitude=longitude, api_key=google_maps_api_key)

@app.route('/view_all_locations_history/<string:email>')
def view_all_locations_history(email):
    selected_date = request.args.get('date')

    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d-%m-%Y")

    # Reference to the employee's location tracking data in Firebase
    
    employee_ref = db.reference(f'employees/{email}/location_tracking')
    location_history = employee_ref.get()
    
    # Prepare a list to store location records for the selected date

    locations = []
    if location_history:
        for date, times in location_history.items():

            if date == formatted_date:  # Filter by selected date
                
                for time, coords in times.items():
                    record = {
                        'latitude': coords.get('latitude'),
                        'longitude': coords.get('longitude'),
                        'time': time
                    }
                    locations.append(record)

    # If no locations are found for the selected date, display a message (optional)
    if not locations:
        flash("No locations found for the selected date.")

    return render_template("view_all_locations_history.html", locations=locations, email=email, api_key=google_maps_api_key)

@app.route('/view_attendance')
def view_attendance():
    attendance_data = []
    employee_ref = db.reference('employees')
    employees = employee_ref.get()

    if employees:
        for email, employee in employees.items():
            if 'attendance' in employee:
                print(f"[INFO] Processing attendance for employee: {employee.get('employee_code', 'Unknown')}")

                for date, record in employee['attendance'].items():
                    print(f"[DEBUG] Record for {date}: {record}")

                    # Safely extract checkin and checkout data
                    checkin_data = record.get("checkin") or {}
                    checkout_data = record.get("checkout") or {}

                    # Debug if check-in or check-out is missing
                    if not checkin_data:
                        print(f"[WARNING] Missing check-in data for {employee.get('employee_code')} on {date}")
                    if not checkout_data:
                        print(f"[WARNING] Missing check-out data for {employee.get('employee_code')} on {date}")

                    attendance_data.append({
                        'name': employee.get('name', 'N/A'),
                        'employee_code': employee.get('employee_code', 'N/A'),
                        'date': date,
                        'check_in': checkin_data.get("time"),
                        'check_out': checkout_data.get("time"),
                        'check_in_image_url': checkin_data.get("photoUrl"),
                        'check_out_image_url': checkout_data.get("photoUrl")
                    })

    print(f"[INFO] Final attendance data: {attendance_data}")
    return render_template('view_attendance.html', attendance=attendance_data)



@app.route('/view_leaves')
def view_leaves():
    leaves_data = []
    employee_ref = db.reference('employees')
    employees = employee_ref.get()
    if employees:
        for email, employee in employees.items():
            if 'leaves' in employee:
                for date, record in employee['leaves'].items():
                    leaves_data.append({
                        'name': employee.get('name', 'N/A'),
                        'employee_code': employee.get('employee_code', 'N/A'),
                        'date': date,
                        'startdate': record.get('startdate', 'N/A'),
                        'enddate': record.get('enddate', 'N/A'),
                        'reason': record.get('reason', 'N/A')
                    })
    return render_template('view_leaves.html', leaves=leaves_data)

@app.route('/add_employee_category', methods=['GET', 'POST'])
def add_employee_category():

    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    if request.method == "POST":
        categoryname = request.form["categoryname"]
        checkintime = request.form["checkintime"]
        checkouttime = request.form["checkouttime"]

        new_category = {
            'categoryname': categoryname,
            'checkintime': checkintime,
            'checkouttime': checkouttime,
        }

        try:
            ref = db.reference(f'/categories/{categoryname}')
            existing_category = ref.get()  # Check if employee already exists

            if existing_category:
                flash('Category with this name already exists!', 'warning')
            else:
                ref.set(new_category)
                flash('Category added successfully!', 'success')
            
        except Exception as e:
            flash('Failed to add category!', 'danger')

        print(categoryname,checkintime, checkouttime)
 
    return render_template('add_employee_category.html')

@app.route('/view_employee_category')
def view_employee_category():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    ref = db.reference('categories')
    categories = ref.get()

    print(categories)

    return render_template('view_employee_category.html', categories=categories)

@app.route('/edit_employee_category/<categoryname>', methods=['GET', 'POST'])
def edit_employee_category(categoryname):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    ref = db.reference(f'/categories/{categoryname}')
    category = ref.get()

    if not category:
        flash("Category not found!", "danger")
        return redirect(url_for('view_employee_category'))

    if request.method == "POST":
        new_categoryname = request.form["categoryname"]
        checkintime = request.form["checkintime"]
        checkouttime = request.form["checkouttime"]

        # If category name is changed, create new record and delete old one
        if new_categoryname != categoryname:
            new_ref = db.reference(f'/categories/{new_categoryname}')
            new_ref.set({
                'categoryname': new_categoryname,
                'checkintime': checkintime,
                'checkouttime': checkouttime,
            })
            ref.delete()  # Remove old category
        else:
            ref.update({
                'checkintime': checkintime,
                'checkouttime': checkouttime
            })

        flash("Category updated successfully!", "success")
        return redirect(url_for('view_employee_category'))

    return render_template('edit_employee_category.html', category=category)


@app.route('/delete_employee_category/<categoryname>')
def delete_employee_category(categoryname):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    ref = db.reference(f'/categories/{categoryname}')
    if ref.get():
        ref.delete()
        flash("Category deleted successfully!", "success")
    else:
        flash("Category not found!", "danger")

    return redirect(url_for('view_employee_category'))

@app.route('/add_unit', methods=['GET', 'POST'])
def add_unit():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    if request.method == "POST":
        unit_name = request.form["unit_name"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        username = request.form["username"]
        password = request.form["password"]

        new_unit = {
            'unit_name': unit_name,
            'latitude': latitude,
            'longitude': longitude,
            'username': username,
            'password': password
        }

        try:
            ref = db.reference(f'/units/{unit_name}')
            existing_unit = ref.get()

            if existing_unit:
                print('Unit with this name already exists!')
                flash('Unit with this name already exists!', 'warning')
            else:
                ref.set(new_unit)
                print('Unit added successfully!')
                flash('Unit added successfully!', 'success')

        except Exception as e:
            print('Failed to add unit!',e)
            flash('Failed to add unit!', 'danger')

    return render_template('add_unit.html')


@app.route('/view_units')
def view_units():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    ref = db.reference('units')
    units = ref.get() or {}

    return render_template('view_units.html', units=units)

@app.route('/edit_unit/<string:unit_name>', methods=['GET', 'POST'])
def edit_unit(unit_name):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    ref = db.reference(f'/units/{unit_name}')
    unit = ref.get() or {}

    if not unit:
        flash('Unit not found!', 'danger')
        return redirect(url_for('view_units'))

    if request.method == "POST":
        updated_data = {
            'unit_name': request.form["unit_name"],
            'latitude': request.form["latitude"],
            'longitude': request.form["longitude"],
            'username': request.form["username"],
            'password': request.form["password"]
        }

        try:
            ref.set(updated_data)
            flash('Unit updated successfully!', 'success')
            return redirect(url_for('view_units'))
        except Exception as e:
            flash('Failed to update unit!', 'danger')

    return render_template('edit_unit.html', unit=unit)

@app.route('/delete_unit/<string:unit_name>')
def delete_unit(unit_name):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    ref = db.reference(f'/units/{unit_name}')
    
    try:
        ref.delete()
        flash('Unit deleted successfully!', 'success')
    except Exception as e:
        flash('Failed to delete unit!', 'danger')

    return redirect(url_for('view_units'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# if __name__ == '__main__':
#     app.run(debug=True)

