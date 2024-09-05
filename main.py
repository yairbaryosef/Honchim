import json

from firebase_admin import db
from flask import Flask, render_template, request, redirect, url_for, jsonify
import PresenterRegister.PresenterSignIn
from Entities.Request import Request
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import os


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
    username = request.form.get('username')
    password = request.form.get('password')
    PresenterSignIn.initFirebase()

    # Save username for later use
    with open("DB/id.txt", 'w') as f:
        f.write(username)

    if username == 'Admin@' and password == 'Password123':

        # For now, let's print the requests to the console (for debugging)
        for request in PresenterRegister.PresenterSignIn.get_all_requests():
            print(request)

        # You can also pass the requests to a template to display them on a webpage
        return render_template('ListRequests.html', requests=PresenterRegister.PresenterSignIn.get_all_requests())
    elif db.reference('Users').child('חניך').child(username).get() is not None:
        # If user exists, save the username in a file and redirect to SignIn

        return render_template('HomePage.html')
    elif db.reference('Users').child('חונך').child(username).get() is not None:
        return render_template('HomePage.html')
        # User does not exist

    else:
        # Check if user is a Cadet or Mentor
        user = db.reference('Users').child('חניך').child(username).get() or \
               db.reference('Users').child('חונך').child(username).get()

        if user:
            if check_password_hash(user['password'], password):
                return render_template('HomePage.html')
        else:
            # If user does not exist, redirect to SignIn
            return redirect(url_for('SignIn'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Extract form data
        form_data = {
            'id': request.form['id'],
            'name': request.form['name'],
            'password': request.form['password'],
            'type': request.form['type']
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

        if grades:
            grades_filename = secure_filename(grades.filename)
            grades_local_path = os.path.join(app.config['UPLOAD_FOLDER'], grades_filename)
            grades.save(grades_local_path)

        # Handle the registration
        return PresenterRegister.handle_registration_form(form_data, profile_local_path, grades_local_path)

    return render_template('Register.html')




# SignIn route
@app.route('/SignIn', methods=['GET', 'POST'])
def SignIn():
    if request.method == 'POST':
        try:
            # Get form data
            user_data = {
                'type': request.form['type'],
                'year': request.form['year'],
                'degree': request.form['degree'],
                'university': request.form['university'],
                'phone': request.form['phone'],
                'help': request.form['help'],
                'description': request.form['description'],
            }

            # Handle file uploads
            profile_picture = request.files['profile-picture']
            grades = request.files['grades']

            # Secure filenames
            profile_filename = secure_filename(profile_picture.filename)
            grades_filename = secure_filename(grades.filename)

            # Define local paths
            profile_local_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_filename)
            grades_local_path = os.path.join(app.config['UPLOAD_FOLDER'], grades_filename)

            # Save files locally
            profile_picture.save(profile_local_path)
            grades.save(grades_local_path)

            # Upload files to Firebase Storage and save request data in Firebase Realtime Database
            PresenterSignIn.saveRequest(
                profile_local_path=profile_local_path,
                grades_local_path=grades_local_path,
                **user_data
            )

            # Redirect to the SignIn page after form submission
            return redirect(url_for('SignIn'))

        except Exception as e:
            print(f"Error during sign in: {e}")
            return render_template('error.html', message="There was an error processing your request.")

    # If GET request, render the form page
    return render_template('SignAsCadetOrElder.html')

# Entrance route
@app.route('/entrance', methods=['POST'])
def entrance():
    return render_template('SignAsCadetOrElder.html')


@app.route('/handle_request/<action>', methods=['GET'])
def handle_request(action):
    request_data = json.loads(request.args.get('request'))
    return PresenterRegister.PresenterSignIn.handle_request(request_data,action)


if __name__ == '__main__':
    app.run(debug=True)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="An unexpected error occurred"), 500