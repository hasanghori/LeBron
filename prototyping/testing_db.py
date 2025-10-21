import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
except:
    pass

# Initialize Firebase Admin SDK
# Replace 'path/to/your/serviceAccountKey.json' with the actual path
cred_info = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
cred = credentials.Certificate(cred_info)
firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Simple Command: Print out all users in the database ---
def print_all_users():
    users_ref = db.collection('users') # Assuming your user data is in a 'users' collection
    docs = users_ref.stream()

    print("--- Current Users in Database ---")
    for doc in docs:
        print(f"User ID: {doc.id}")
        print(f"  Data: {doc.to_dict()}")
    print("---------------------------------")

# --- Simple Command: Write a new user to the database ---
def add_new_user(user_id, phone_number, notion_api, user_interests):
    doc_ref = db.collection('users').document(user_id) # Set the document ID
    doc_ref.set({
        'PhoneNumber': phone_number,
        'NotionAPI': notion_api,
        'UserInterests': user_interests
    })
    print(f"Successfully added user: {user_id}")

# --- Example Usage (you can call these functions from your Flask routes) ---
if __name__ == '__main__':
    print_all_users()

    # Add a new user (example data)
    add_new_user(
        user_id='flask_user_001',
        phone_number='+15551234567',
        notion_api='FLASK-API-KEY-123',
        user_interests=['coding', 'web_dev', 'python']
    )

    # Print again to see the newly added user
    print("\nAfter adding new user:")
    print_all_users()
