from flask import Flask, render_template, request, redirect, url_for
import PresenterRegister.PresenterSignIn
from Entities.Request import Request
from werkzeug.utils import secure_filename
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
    from flask import request
    username = request.form.get('username')
    password=request.form.get('password')
    if username=='Admin@' and password=='Password123':

            # For now, let's print the requests to the console (for debugging)
            for request in  PresenterRegister.PresenterSignIn.get_all_requests():
                print(request)

            # You can also pass the requests to a template to display them on a webpage
            return render_template('ListRequests.html', requests=PresenterRegister.PresenterSignIn.get_all_requests())

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


if __name__ == '__main__':
    app.run(debug=True)
