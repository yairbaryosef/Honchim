import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import timedelta
import os

from flask import jsonify


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

def saveRequest(profile_local_path, grades_local_path, type, year, degree, uni, phone, help, description):
    initFirebase()

    # Get the storage bucket
    bucket = storage.bucket()

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
    with open("DB\id.txt",'r') as f:
     id=f.read()
    # Create a new Request object and save it in Firebase Realtime Database
    new_request_ref = db.reference('Requests').child(id)
    new_request_ref.set({
        'id':id,
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

    # Optionally, delete the local files after uploading to Firebase
    os.remove(profile_local_path)
    os.remove(grades_local_path)

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
