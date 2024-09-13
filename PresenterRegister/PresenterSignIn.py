import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import timedelta
import os
import PresenterRegister

from flask import jsonify, render_template, url_for, redirect


def initFirebase():
    # Path to your service account key JSON file
    firebase_key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DB', 'FirebaseKey.json'))

    cred = credentials.Certificate(firebase_key_path)

    try:
        # Attempt to initialize the Firebase app
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://honchim-449da-default-rtdb.europe-west1.firebasedatabase.app/",
            "storageBucket": "honchim-449da.appspot.com"  # Replace with your actual bucket name
        })
    except ValueError:
        # If the app is already initialized, this will catch the error
        print("Firebase app already initialized, skipping reinitialization.")

def saveRequest(profile_local_path, grades_local_path, id, name, password, type, year, degree, uni, phone, help, description):
    initFirebase()

    # Get the storage bucket
    bucket = storage.bucket()

    try:
        # Check if the files exist
        if not os.path.exists(profile_local_path) or not os.path.exists(grades_local_path):
            raise FileNotFoundError("One or more files were not found.")

        # Define filenames for storage
        profile_filename = os.path.basename(profile_local_path)
        grades_filename = os.path.basename(grades_local_path)

        # Create blob objects for Firebase Storage
        profile_blob = bucket.blob(f'profiles/{profile_filename}')
        grades_blob = bucket.blob(f'grades/{grades_filename}')

        # Upload files to Firebase Storage
        profile_blob.upload_from_filename(profile_local_path)
        grades_blob.upload_from_filename(grades_local_path)

        # Get the public URLs of the uploaded files
        profile_url = profile_blob.generate_signed_url(timedelta(days=7), method='GET')
        grades_url = grades_blob.generate_signed_url(timedelta(days=7), method='GET')
    except FileNotFoundError as e:
         # Handle the case where the files were not found
        print(f"Error during file upload: {e}")
        #return jsonify({'status': 'error', 'message': 'One or more files were not found.'})

    # Check if the user already exists in the database
    if not checkIfUserIdExist(id):
        new_user = db.reference('Users').child(type).child(id)
        new_user.set({
            'id': id,
            'name': name,
            'password': password,
            'type': 'מחכה לאישור',
        })
    print("User created successfully.")
    # Create a new Request object and save it in Firebase Realtime Database
    if checkIfUserRequestExist(id):
        return jsonify({'status': 'error', 'message': 'A request has already been made with this ID. Please wait for approval.'})
    new_request_ref = db.reference('Requests').child(id)
    new_request_ref.set({
        'id': id,
        'type': type,
        'year': year,
        'degree': degree,
        'uni': uni,
        'phone': phone,
        'help': help,
        'description': description,
        'profile_url': profile_url,
        'grades_url': grades_url
    })
    print("Request saved successfully.")

    # Optionally, delete the local files after uploading to Firebase
    #os.remove(profile_local_path)
    #os.remove(grades_local_path)

    return jsonify({'status': 'success', 'message': 'Request saved successfully.'})

def handle_request(request_data,action):
    initFirebase()
    db.reference('Requests').child(request_data['id']).delete()
    # Perform your logic based on action ('accept' or 'cancel')
    if action == 'accept':
        db.reference('Users').child(request_data['type']).child(request_data['id']).set(request_data)
        # Handle accept logic
        print("Accepted request:", request_data)
    elif action == 'cancel':
        # Handle cancel logic
        print("Cancelled request:", request_data)

    # Return a response
    return jsonify({'status': 'success', 'action': action})
def get_all_requests():
            initFirebase()
            # Reference to the 'Requests' node in the database
            ref = db.reference('Requests')

            # Fetch all request objects
            all_requests = ref.get()

            # Check if there are any requests
            if all_requests:
                # Convert the data into a list of dictionaries (if needed)
                requests_list = list(all_requests.values())
            else:
                requests_list = []
            return requests_list

def checkIfUserIdExist(id):
    initFirebase()
    for type in ['חניך', 'חונך']:
        if db.reference('Users').child(type).child(id).get() is not None:
            return True
    return False
    
def checkIfUserRequestExist(id):
    initFirebase()
    if db.reference('Requests').child(id).get() is not None:
        return True
    else:
        return False

def checkIfUserExist(username,password):
    initFirebase()
    with open("DB/id.txt", 'w') as f:
        f.write(username)
    if username=='Admin@' and password=='Password123':

            # For now, let's print the requests to the console (for debugging)
            for request in  PresenterRegister.PresenterSignIn.get_all_requests():
                print(request)

            # You can also pass the requests to a template to display them on a webpage
            return render_template('ListRequests.html', requests=PresenterRegister.PresenterSignIn.get_all_requests())
    elif db.reference('חניך').child(username).get() is not None:
            # If user exists, save the username in a file and redirect to SignIn

            return render_template('HomePage.html')
    elif db.reference('חונך').child(username).get() is not None:
        return render_template('HomePage.html')
            # User does not exist

    else:
        # Handle the case where the user does not exist
        return redirect(url_for('SignIn'))
if __name__ == '__main__':
    # Example usage of saveRequest
    saveRequest(
        profile_local_path='/path/to/local/profile_picture.jpg',
        grades_local_path='/path/to/local/grades.pdf',
        type='חונך',
        year=3,
        degree='Computer Science',
        uni='Ben Gurion University',
        phone='1234567890',
        help='Help with programming',
        description='Looking for assistance in advanced algorithms.'
    )
