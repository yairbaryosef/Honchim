import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import timedelta
import os
from werkzeug.security import generate_password_hash
from flask import jsonify, render_template, redirect, url_for

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

def registerUser(user_id, name, password, user_type, profile_local_path=None, grades_local_path=None):
    initFirebase()

    # Check if the user already exists
    if db.reference(f'Users/{user_type}').child(user_id).get() is not None:
        print(f"User with ID {user_id} already exists.")
        return False
    
    hashed_password  = generate_password_hash(password)

    # Get the storage bucket
    bucket = storage.bucket()

    # Upload files to Firebase Storage, if they exist
    profile_url = None
    grades_url = None

    if profile_local_path:
        profile_filename = os.path.basename(profile_local_path)
        profile_blob = bucket.blob(f'profiles/{profile_filename}')
        profile_blob.upload_from_filename(profile_local_path)
        profile_url = profile_blob.generate_signed_url(timedelta(days=7), method='GET')

    if grades_local_path:
        grades_filename = os.path.basename(grades_local_path)
        grades_blob = bucket.blob(f'grades/{grades_filename}')
        grades_blob.upload_from_filename(grades_local_path)
        grades_url = grades_blob.generate_signed_url(timedelta(days=7), method='GET')

    # Save the user details in Firebase Realtime Database
    new_user_ref = db.reference(f'Users/{user_type}').child(user_id)
    new_user_ref.set({
        'name': name,
        'password': hashed_password,  
        'type': user_type,
        'profile_url': profile_url,
        'grades_url': grades_url
    })

    # Optionally, delete the local files after uploading to Firebase
    if profile_local_path:
        os.remove(profile_local_path)
    if grades_local_path:
        os.remove(grades_local_path)

    print(f"Successfully registered user: {user_id}")
    return True

def handle_registration_form(form_data, profile_local_path=None, grades_local_path=None):
    user_id = form_data['id']
    name = form_data['name']
    password = form_data['password']
    user_type = form_data['type']

    if registerUser(user_id, name, password, user_type, profile_local_path, grades_local_path):
        return render_template('HomePage.html')
    else:
        return render_template('Register.html', error="User already exists.")

if __name__ == '__main__':
    # Example usage of registerUser
    registerUser(
        user_id='1234567890',
        name='John Doe',
        password='securepassword',
        user_type='חונך',
        profile_local_path='/path/to/local/profile_picture.jpg',
        grades_local_path='/path/to/local/grades.pdf'
    )
