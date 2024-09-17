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

        if user is None:
            return render_template('SignAsCadetOrElder.html')

        #   if not (user and check_password_hash(user['password'], password)):  # Verify hashed password
      #      return render_template('login.html', error="Invalid username or password.")
       # else:
        with open("DB/user.json", 'w') as f:
            json.dump(user, f)

        session['id'] = username
        return redirect(url_for('HomePage'))
    
    return render_template('login.html')
        
@app.route('/HomePage', methods=['GET', 'POST'])   
def HomePage():
    if 'id' not in session or not PresenterSignIn.checkIfUserIdExist(session['id']):
        return redirect(url_for('home'))
    user = db.reference('Users').child('חניך').child(session['id']).get() or \
              db.reference('Users').child('חונך').child(session['id']).get() or \
                db.reference('Users').child('מחכה לאישור').child(session['id']).get()
    name = user.get('name')

    if 'חניך' == user['type']:
        return render_template('CadetHomePage.html', name = name)
    # TODO: FINISH חונך
    elif 'חונך' == user['type']:
        return render_template('ElderHomePage.html')
    elif 'מחכה לאישור' == user['type']:
        IsPending = PresenterSignIn.checkIfUserRequestExist(session['id'])
        return render_template('PendingHomePage.html', name = name, status = IsPending)
    else:
        return render_template('error.html', message="User not found")
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
            with open("DB/id.txt", 'r') as f:
                user=f.read()
            # Extract form data
            form_data = {
                'id': user,
                'name': "name",
                'password': "123",
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

from datetime import datetime


@app.route('/create_class', methods=['GET', 'POST'])
def move_to_create_class():
    # Read JSON data from file
    with open("DB/user.json", 'r') as f:
        user = json.load(f)  # Correctly loads the JSON data into a Python dictionary
    user.setdefault('name', 'DefaultName')
    # Construct the URL for the RequestClass endpoint
    return redirect(url_for('RequestClass', elder_name=user['name'], elder_id=user['id']))


@app.route('/contact', methods=['GET'])
def contact_elder():
    elder_id = request.args.get('id')  # Get the 'id' parameter from the query string
    print(f"Received elder ID: {elder_id}")
    with open("DB/user.json", 'r') as f:
        data = json.load(f)
    # Log the ID for debugging
    db.reference('Users').child('חונך').child(elder_id).child('students').push(data['id'])
    return f"הוסםת את עצמך בהצלחה למשתמש: {elder_id}"

# Send Class route
@app.route('/RequestClass/<elder_name>/<elder_id>', methods=['GET', 'POST'])
def RequestClass(elder_name, elder_id):
    if 'id' not in session:
        return redirect(url_for('home'))
    PresenterSignIn.initFirebase()
    # Fetch the elder's details using the elder_id
    elder_ref = db.reference('Users').child('חונך').child(elder_id)
    elder = elder_ref.get()


    if request.method == 'POST':
        # Extract form data
        date_start = request.form.get('date_start')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        # Combine the date with the times
        date_start_combined = date_start + ' ' + start_time
        date_end_combined = date_start + ' ' + end_time

        notes = request.form.get('notes')

        # Retrieve cadet ID from session
        cadet_id = session['id']

        # Format the dates
        date_format = "%Y-%m-%d %H:%M"
        date_start_parsed = datetime.strptime(date_start_combined, date_format)
        date_end_parsed = datetime.strptime(date_end_combined, date_format)

        formatted_date_start = date_start_parsed.strftime("%d/%m/%Y %I:%M %p")
        formatted_date_end = date_end_parsed.strftime("%d/%m/%Y %I:%M %p")

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
        cadet=db.reference('Users').child('חניך').child(cadet_id).get()
        cadet.classes_to_aprove.append(new_class)
        db.reference('Users').child('חניך').child(cadet_id).set(cadet)


        return render_template('request_class_success.html', elder=elder)

    # For GET requests, render the class request form
    return render_template('CreateClass.html', elder_name=elder_name, elder_id=elder_id)

@app.route('/SendClass', methods=['POST'])
def SendClass():
    if request.method == 'POST':
        try:
            PresenterSignIn.initFirebase()
        except Exception as e:
            print(f"Firebase initialization error: {e}")  # Handle the initialization issue

        # Get data from the form
        student_username = request.form.get('student_username')
        date_start_str = request.form.get('dateStart')
        date_end_str = request.form.get('dateEnd')
        with open("DB/user.json", 'r') as f:
            user = json.load(f)
        teacher = user['id']
        print(user['students'].values())
        if student_username not in user['students'].values():
            return "User does not belong to you"

        # Replace with actual teacher info if available

        # Check if any of the required fields are missing
        if not student_username or not date_start_str or not date_end_str:
            return jsonify({"error": "Missing required form fields"}), 400

        # Correct date format for parsing
        date_format = "%Y-%m-%dT%H:%M"

        try:

            # Convert the strings to datetime objects
            date_start = datetime.strptime(date_start_str, date_format)
            date_end = datetime.strptime(date_end_str, date_format)

            # Reformat dates to match the desired output format
            formatted_date_start = date_start.strftime("%d/%m/%Y %I:%M %p")
            formatted_date_end = date_end.strftime("%d/%m/%Y %I:%M %p")

            # Create the new class dictionary with formatted dates
            new_class = {
                "teacher": teacher,
                "dateStart": formatted_date_start,
                "dateEnd": formatted_date_end
            }

            # Retrieve the student from Firebase
            student_ref = db.reference('Users').child('חניך').child(student_username)
            student_data = student_ref.get()

            # Add new class to the student's classes_to_approve list
            if student_data:
                if 'classes_to_aprove' not in student_data:
                    student_data['classes_to_aprove'] = []
                student_data['classes_to_aprove'].append(new_class)
                student_ref.set(student_data)

            return jsonify({"message": "Class added successfully"}), 200

        except ValueError as ve:
            return jsonify({"error": f"Invalid date format: {ve}"}), 400

        except Exception as e:
            return jsonify({"error": f"An error occurred: {e}"}), 500

    return jsonify({"error": "Invalid request method"}), 405




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
    elders = [elder for elder in elders if elder is not None]
    if elders:
        for elder in elders:
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

