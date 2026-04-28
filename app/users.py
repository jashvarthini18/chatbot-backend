# import json
# import os

# USERS_FILE = "users.json"

# def load_users():
#     if not os.path.exists(USERS_FILE):
#         with open(USERS_FILE, "w") as f:
#             json.dump([], f)
#         return []

#     with open(USERS_FILE, "r") as f:
#         return json.load(f)


# def save_users(users):
#     with open(USERS_FILE, "w") as f:
#         json.dump(users, f, indent=2)


# def get_user_by_email(email: str):
#     users = load_users()
#     return next((u for u in users if u["email"] == email), None)


# def create_user(email: str, hashed_password: str):
#     users = load_users()
#     users.append({
#         "email": email,
#         "password": hashed_password
#     })
#     save_users(users)
import json
import os

# ✅ FIX: absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "..", "users.json")
print("USERS FILE PATH =", os.path.abspath(USERS_FILE))


def load_users():
    try:
        if not os.path.exists(USERS_FILE):
            print("users.json not found, creating new file")
            with open(USERS_FILE, "w") as f:
                json.dump([], f)
            return []

        with open(USERS_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)

    except Exception as e:
        print("LOAD USERS ERROR:", str(e))
        return []


def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print("SAVE USERS ERROR:", str(e))


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

