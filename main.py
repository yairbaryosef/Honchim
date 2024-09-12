import json
from datetime import datetime
from firebase_admin import db
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename
import os
import PresenterRegister.PresenterSignIn as PresenterSignIn
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
from flask import make_response
import difflib


# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('home'))


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        PresenterSignIn.initFirebase()

        with open("DB/id.txt", 'w') as f:
            f.write(username)

        if username == 'Admin@' and password == 'Password123':
            requests = PresenterSignIn.get_all_requests()
            return render_template('ListRequests.html', requests=requests)

        user = db.reference('Users').child('חניך').child(username).get() or \
                db.reference('Users').child('חונך').child(username).get() or \
                db.reference('Users').child('מחכה לאישור').child(username).get()

        if not (user and check_password_hash(user['password'], password)):  # Verify hashed password
            return render_template('login.html', error="Invalid username or password.")
        else:
            session['id'] = username
            return redirect(url_for('HomePage'))
    
    return render_template('login.html')
        
@app.route('/HomePage', methods=['GET', 'POST'])   
def HomePage():
    if 'id' not in session:
        return redirect(url_for('home'))
    user = db.reference('Users').child('חניך').child(session['id']).get() or \
              db.reference('Users').child('חונך').child(session['id']).get() or \
                db.reference('Users').child('מחכה לאישור').child(session['id']).get()
    name = user.get('name')
    if 'חניך' in user or True:
        return render_template('CadetHomePage.html', name = name)
    elif 'חונך' in data:
        return render_template('ElderHomePage.html')
    else:
        IsPending = PresenterSignIn.checkIfUserRequestExist(session['id'])
        return render_template('PendingHomePage.html', name = name, status = IsPending)
# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('RegisterStep1.html')

# Register route
@app.route('/register_step1', methods=['GET', 'POST'])
def register1():
    if request.method == 'POST':
        try:
            # Store first part of the registration data in session
            session['id'] = request.form['id']
            if PresenterSignIn.checkIfUserIdExist(session['id']):
                return render_template('RegisterStep1.html', error="User ID already exists.")
            session['name'] = request.form['name']
            session['password'] = generate_password_hash(request.form['password'])  # Hashing the password
            return redirect(url_for('register2'))
        except Exception as e:
            print(f"Error during registration step 1: {e}")
            return render_template('error.html', message="There was an error processing your registration.")

    return render_template('RegisterStep1.html')

# Second step of registration
@app.route('/register_step2', methods=['GET', 'POST'])
def register2():
    if request.method == 'POST':
        try:
            # Extract form data
            form_data = {
                'id': session['id'],
                'name': session['name'],
                'password': session['password'],
                'type': request.form['type'],
                'year': request.form['year'],
                'degree': request.form['degree'],
                'uni': request.form['university'],
                'phone': request.form['phone'],
                'help': request.form['help'],
                'description': request.form['description']
            }

            # Handle file uploads, check if the files were uploaded
            profile_picture = request.files.get('profile-picture')
            grades = request.files.get('grades')

            profile_local_path = None
            grades_local_path = None

            if profile_picture:
                profile_filename = secure_filename(profile_picture.filename)
                profile_local_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_filename)
                profile_picture.save(profile_local_path)
            else:
                return render_template('RegisterStep2.html', error="Profile picture is required.")

            if grades:
                grades_filename = secure_filename(grades.filename)
                grades_local_path = os.path.join(app.config['UPLOAD_FOLDER'], grades_filename)
                grades.save(grades_local_path)
            else:
                return render_template('RegisterStep2.html', error="Grades file is required.")

            # Save the request for admin approval
            response = PresenterSignIn.saveRequest(profile_local_path, grades_local_path, **form_data)

            # Check response and handle error if a request already exists
            if response.get_json()['status'] == 'error':
                print(f"Error during registration step 2: {response.get_json()['message']}")
                return render_template('RegisterStep2.html', error=response.get_json()['message'])

            # Clear session data after saving the request
            type = form_data['type']
            session.clear()

            print(f"Registration successful for {form_data['name']} with ID {form_data['id']}")

            # only for testing
            if type == 'חניך':
                return render_template('PendingHomePage.html')
            elif type == 'חונך':
                return render_template('ElderHomePage.html')
            # End of testing
            return redirect(url_for('home'))
        except Exception:
            print(f"Error during registration step 2: {traceback.format_exc()}")
            return render_template('error.html', message="There was an error processing your registration.")

    print("Session data:", session)
    return render_template('RegisterStep2.html')



# Classes route
@app.route('/Classes', methods=['GET', 'POST'])
def MyClasses():
    with open("DB/user.json", 'r') as f:
        data = json.load(f)
    students = data.get('classes_to_aprove', [])
    return render_template('MyClasses.html', items=students)

# Send Class route
@app.route('/RequestClass/<elder_name>/<elder_id>', methods=['GET', 'POST'])
def RequestClass(elder_name, elder_id):
    if 'id' not in session:
        return redirect(url_for('home'))

    # Fetch the elder's details using the elder_id
    elder_ref = db.reference('Users').child('חונך').child(elder_id)
    elder = elder_ref.get()

    if not elder or elder.get('name') != elder_name:
        return render_template('error.html', message="Elder not found")

    if request.method == 'POST':
        # Extract form data
        date_start = request.form.get('date_start')
        date_end = request.form.get('date_end')
        notes = request.form.get('notes')

        # Retrieve cadet ID from session
        cadet_id = session['id']

        # Format the dates
        date_format = "%Y-%m-%dT%H:%M"
        date_start = datetime.strptime(date_start, date_format)
        date_end = datetime.strptime(date_end, date_format)

        formatted_date_start = date_start.strftime("%d/%m/%Y %I:%M %p")
        formatted_date_end = date_end.strftime("%d/%m/%Y %I:%M %p")

        # Create the class request
        new_class = {
            "teacher": elder_id,
            "dateStart": formatted_date_start,
            "dateEnd": formatted_date_end,
            "student": cadet_id,
            "notes": notes,
            "status": "pending"
        }

        # Save the request to the elder's record
        if 'class_requests' not in elder:
            elder['class_requests'] = []
        elder['class_requests'].append(new_class)
        elder_ref.set(elder)

        return render_template('request_class_success.html', elder=elder)

    # For GET requests, render the class request form
    return render_template('CreateClass.html', elder_name=elder_name, elder_id=elder_id)


# Handle request route
@app.route('/handle_request/<action>', methods=['GET'])
def handle_request(action):
    request_data = json.loads(request.args.get('request'))
    return PresenterSignIn.handle_request(request_data, action)

# Handle Class Accept route
@app.route('/handle_ClassAccept/<action>', methods=['GET'])
def handle_ClassAccept(action):
    if action == "accept":
        request_data = json.loads(request.args.get('request'))
        date_format = "%d/%m/%Y %I:%M %p"

        date_start = datetime.strptime(request_data['dateStart'].strip(), date_format)
        date_end = datetime.strptime(request_data['dateEnd'].strip(), date_format)

        time_difference = date_end - date_start
        difference_in_hours = time_difference.total_seconds() / 3600

        PresenterSignIn.initFirebase()
        user = db.reference('Users').child('חונך').child(request_data['teacher']).get()
        user['hours'] = user.get('hours', 0) + difference_in_hours

        db.reference('Users').child('חונך').child(request_data['teacher']).set(user)
        return jsonify(request_data), 200
    return jsonify({"error": "Invalid action"}), 400

def calculate_similarity(name, query):
    # Calculate similarity ratio using difflib
    print(name, query)
    return difflib.SequenceMatcher(None, name.lower(), query.lower()).ratio()

# Handle cadet elder pairing
@app.route('/search_elders', methods=['GET', 'POST'])
def search_elders():
    if 'id' not in session:
        return redirect(url_for('home'))

    # Get all elders from the database
    elders_ref = db.reference('Users').child('חונך')
    elders = elders_ref.get()

    # Convert the elders data into a list
    elders_list = []
    if elders:
        for key, elder in elders.items():
            if elder.get('type') == 'חונך' or True:
                elder_name = elder.get('name')
                elder['first_name'] = elder_name.split(' ')[0] if elder_name else ''  
                elders_list.append(elder)


    # Handle search and filtering
    if request.method == 'POST':
        search_query = request.form.get('search')
        year = request.form.get('year')
        expertise = request.form.get('expertise')
        degree = request.form.get('degree')
        university = request.form.get('university')

        # Filter elders based on search criteria
        if search_query:

            elders_list = [(elder, calculate_similarity(str(elder.get('name')), search_query)) for elder in elders_list]
            elders_list = sorted(elders_list, key=lambda x: x[1], reverse=True)
            elders_list = [elder[0] for elder in elders_list if elder[1] > 0.3]  # Filter out low similarity scores

        if year:
            elders_list = [elder for elder in elders_list if elder.get('year') == str(year)]

        if expertise:
            elders_list = [elder for elder in elders_list if expertise.lower() in elder.get('help', '').lower()]

        if degree:
            elders_list = [elder for elder in elders_list if degree.lower() in elder.get('degree', '').lower()]

        if university:
            elders_list = [elder for elder in elders_list if university.lower() in elder.get('uni', '').lower()]

    return render_template('CadetSearchForElder.html', elders=elders_list)

if __name__ == '__main__':
    app.run(debug=True)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="An unexpected error occurred"), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
