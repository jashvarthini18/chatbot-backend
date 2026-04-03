import json
import os

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)
        return []

    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_user_by_email(email: str):
    users = load_users()
    return next((u for u in users if u["email"] == email), None)


def create_user(email: str, hashed_password: str):
    users = load_users()
    users.append({
        "email": email,
        "password": hashed_password
    })
    save_users(users)
