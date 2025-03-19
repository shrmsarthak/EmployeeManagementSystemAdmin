from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random key

# Mock admin credentials (you can replace these with a database in the future)
admin_username = 'admin'
admin_password = generate_password_hash('admin') # Hashed password

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

@app.route('/add_employee')
def add_employee():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    return render_template('add_employee.html')

@app.route('/view_employee')
def view_employee():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    return render_template('view_employee.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
