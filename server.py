# import os
# from contextlib import asynccontextmanager
# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# from app import rag, auth, users
# from app.pdf import process_document
# from app.auth import verify_token
# import uvicorn

# # UPLOAD_FOLDER = "uploads"
# # DEFAULT_PDF = os.path.join(UPLOAD_FOLDER, "coalVeer data.pdf")
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
# DEFAULT_PDF = os.path.join(UPLOAD_FOLDER, "coalVeer data.pdf")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Starting backend...")

#     rag.init_llm()
#     loaded = rag.load_faiss_index()

#     if not loaded:
#         if not os.path.exists(DEFAULT_PDF):
#             raise RuntimeError("Default PDF missing")

#         process_document(DEFAULT_PDF, rag.embeddings)
#         rag.load_faiss_index()

#     print("Backend ready")
#     yield


# app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class Message(BaseModel):
#     userMessage: str


# class AuthRequest(BaseModel):
#     email: str
#     password: str


# @app.get("/")
# def health():
#     return {"status": "ok"}


# @app.post("/api/chat")
# async def chat(message: Message, user=Depends(verify_token)):
#     return {"botResponse": rag.process_prompt(message.userMessage)}


# @app.post("/auth/signup", status_code=201)
# async def signup(data: AuthRequest):
#     if users.get_user_by_email(data.email):
#         raise HTTPException(status_code=400, detail="User already exists")

#     hashed = auth.hash_password(data.password)
#     users.create_user(data.email, hashed)

#     return {"message": "User created successfully"}


# @app.post("/auth/login")
# async def login(data: AuthRequest):
#     user = users.get_user_by_email(data.email)

#     if not user or not auth.verify_password(
#         data.password, user["password"]
#     ):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     token = auth.create_access_token({"sub": user["email"]})

#     return {
#         "access_token": token,
#         "token_type": "bearer"
#     }

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import rag, auth, users
from app.pdf import process_document
from app.auth import verify_token

# ---------------- PATH SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DEFAULT_PDF = os.path.join(UPLOAD_FOLDER, "coalVeer data.pdf")

# ---------------- APP INIT ----------------
app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://chatbot-frontend-iota-jet.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- GLOBAL FLAG ----------------
initialized = False

# ---------------- MODELS ----------------
class Message(BaseModel):
    userMessage: str


class AuthRequest(BaseModel):
    email: str
    password: str


# ---------------- HEALTH ----------------
@app.get("/")
def health():
    return {"status": "ok"}


# ---------------- CHAT (LAZY LOAD HERE) ----------------
@app.post("/api/chat")
async def chat(message: Message, user=Depends(verify_token)):
    global initialized

    # 🔥 Lazy initialization (FIX)
    if not initialized:
        print("Initializing backend (first request)...")

        rag.init_llm()
        loaded = rag.load_faiss_index()

        if not loaded:
            if os.path.exists(DEFAULT_PDF):
                process_document(DEFAULT_PDF, rag.embeddings)
                rag.load_faiss_index()
            else:
                print("⚠️ Default PDF not found, skipping")

        initialized = True
        print("Backend initialized successfully")

    return {"botResponse": rag.process_prompt(message.userMessage)}


# ---------------- AUTH ----------------
@app.post("/auth/signup", status_code=201)
async def signup(data: AuthRequest):
    if users.get_user_by_email(data.email):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = auth.hash_password(data.password)
    users.create_user(data.email, hashed)

    return {"message": "User created successfully"}


@app.post("/auth/login")
async def login(data: AuthRequest):
    user = users.get_user_by_email(data.email)

    if not user or not auth.verify_password(
        data.password, user["password"]
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"sub": user["email"]})

    return {
        "access_token": token,
        "token_type": "bearer"
    }



if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)