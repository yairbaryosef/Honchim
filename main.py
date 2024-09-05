import json
from datetime import datetime

from firebase_admin import db
from flask import Flask, render_template, request, redirect, url_for, jsonify

import Entities.Elder
import PresenterRegister.PresenterSignIn
from Entities.Request import Request
from werkzeug.utils import secure_filename
import os

from PresenterRegister import PresenterSignIn

# Initialize the Flask application
app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Home route
@app.route('/', methods=['GET', 'POST'])
def home():

    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    from flask import request
    username = request.form.get('username')
    password=request.form.get('password')
    PresenterSignIn.initFirebase()
    with open("DB/id.txt", 'w') as f:
        f.write(username)
    if username == 'Admin@' and password == 'Password123':

        # For now, let's print the requests to the console (for debugging)
        for request in PresenterRegister.PresenterSignIn.get_all_requests():
            print(request)

        # You can also pass the requests to a template to display them on a webpage
        return render_template('ListRequests.html', requests=PresenterRegister.PresenterSignIn.get_all_requests())
    elif db.reference('Users').child('חניך').child(username).get() is not None:
        user = db.reference('Users').child('חניך').child(username).get()

        with open('DB/user.json','w') as f:
            json.dump(user, f)  #
        return render_template('HomePage.html')
    elif db.reference('Users').child('חונך').child(username).get() is not None:
        user=db.reference('Users').child('חונך').child(username).get()
        with open('DB/user.json', 'w') as f:
            json.dump(user, f)  #
        return render_template('CreateClass.html')
        # User does not exist

    else:
        # Handle the case where the user does not exist
        return redirect(url_for('SignIn'))
# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():

    return render_template('Register.html')

# SignIn route
@app.route('/SignIn', methods=['GET', 'POST'])
def SignIn():
    if request.method == 'POST':
        # Get form data
        type = request.form['type']
        year = request.form['year']
        degree = request.form['degree']
        uni = request.form['university']
        phone = request.form['phone']
        help = request.form['help']
        description = request.form['description']

        # Handle file uploads
        profile_picture = request.files['profile-picture']
        grades = request.files['grades']

        # Secure and save the uploaded files locally first
        profile_filename = secure_filename(profile_picture.filename)
        grades_filename = secure_filename(grades.filename)

        # Define paths for local saving (this is temporary, just before upload)
        profile_local_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_filename)
        grades_local_path = os.path.join(app.config['UPLOAD_FOLDER'], grades_filename)

        # Save files locally
        profile_picture.save(profile_local_path)
        grades.save(grades_local_path)

        # Upload files to Firebase Storage and save request data in Firebase Realtime Database
        PresenterRegister.PresenterSignIn.saveRequest(
            profile_local_path=profile_local_path,
            grades_local_path=grades_local_path,
            type=type,
            year=year,
            degree=degree,
            uni=uni,
            phone=phone,
            help=help,
            description=description
        )

        # Redirect to the SignIn page after form submission
        return redirect(url_for('SignIn'))

    # If GET request, render the form page
    return render_template('SignAsCadetOrElder.html')

# Entrance route
@app.route('/entrance', methods=['POST'])
def entrance():
    return render_template('SignAsCadetOrElder.html')

@app.route('/Classes', methods=['GET', 'POST'])
def MyClasses():
    with open("DB/user.json",'r') as f:
        data = json.load(f)
    try:
        students=data['classes_to_aprove']

    except:
        students=[]
    return render_template('MyClasses.html', items=students)


@app.route('/SendClass', methods=['POST'])
def SendClass():
    # Initialize Firebase
    PresenterSignIn.initFirebase()

    # Parse JSON data from the request
    data = request.get_json()

    # Extract the student username and class details
    student_username = data.get('student_username')
    date_format = "%Y-%m-%dT%H:%M"
    date_start = data.get('dateStart')
    date_end = data.get('dateEnd')

    if not student_username:
        return jsonify({"error": "Student username is required"}), 400

    # Get a reference to the student in the Firebase database
    student_ref = db.reference('Users').child('חניך').child(student_username)

    # Fetch current student data
    student = student_ref.get()
    date_start = datetime.strptime(date_start, date_format)
    date_end = datetime.strptime(date_end, date_format)

    # Reformat dates to match the desired output format

    # Check if the student exists
    if not student:
        return jsonify({"error": "Student not found"}), 404
    with open('DB/id.txt','r') as f:
        teacher=f.read()
    # Prepare the new class data to be added
    formatted_date_start = date_start.strftime("%d/%m/%Y %I:%M %p")
    formatted_date_end = date_end.strftime("%d/%m/%Y %I:%M %p")

    # Create the new class dictionary with formatted dates
    new_class = {
        "teacher": teacher,
        "dateStart": formatted_date_start,
        "dateEnd": formatted_date_end
    }

    # Update the student's 'classes_to_approve' list
    classes_to_approve = student.get('classes_to_aprove', [])
    classes_to_approve.append(new_class)

    # Save the updated list back to Firebase
    student['classes_to_aprove'] = classes_to_approve
    student_ref.set(student)

    return jsonify({"message": "Class added successfully"}), 200


@app.route('/handle_request/<action>', methods=['GET'])
def handle_request(action):
    # Parse the request data from the URL parameter
    request_data = json.loads(request.args.get('request'))
    return PresenterRegister.PresenterSignIn.handle_request(request_data,action)

@app.route('/handle_ClassAccept/<action>', methods=['GET'])
def handle_ClassAccept(action):
    # Parse the request data from the URL parameter
  if action == "accept":
    request_data = json.loads(request.args.get('request'))
    date_format = "%d/%m/%Y %I:%M %p"

    # Convert the strings to datetime objects
    date_start = datetime.strptime(request_data['dateStart'].strip(), date_format)
    date_end = datetime.strptime(request_data['dateEnd'].strip(), date_format)

    # Subtract the two dates
    time_difference = date_end - date_start
    PresenterSignIn.initFirebase()
    # Display the difference
    difference_in_hours = time_difference.total_seconds() / 3600
    print(request_data['teacher'])
    user = db.reference('Users').child('חונך').child(request_data['teacher']).get()
    print(user)
    user['hours'] = user.get('hours', 0) + difference_in_hours


    db.reference('Users').child('חונך').child(request_data['teacher']).set(user)
    return request_data
  return action


if __name__ == '__main__':
    app.run(debug=True)
