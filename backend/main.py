from fastapi import FastAPI, UploadFile, Form, BackgroundTasks, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from email_sender import send_bulk_email
from whatsapp_sender import send_bulk_whatsapp
from email_sender import router as email_router
from whatsapp_sender import router as whatsapp_router
from oauth import router as oauth_router, get_user_token
import shutil
import os

app = FastAPI()

# CORS middleware (if frontend is hosted separately)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(oauth_router, prefix="/auth")
app.include_router(email_router, prefix="/send-email")
app.include_router(whatsapp_router, prefix="/send-whatsapp")

@app.get("/")
def root():
    return {"message": "Mass Messaging Backend is running"}

# ✅ Route to send email after user has authenticated via Google OAuth
@app.post("/send-email/")
async def email_handler(
    request: Request,
    file: UploadFile,
    subject: str = Form(...),
    body: str = Form(...),
    token: str = Depends(get_user_token),  # Get token from cookie/session/header
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    file_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(send_bulk_email, file_path, subject, body, token)
    return {"status": "Email sending started"}

# ✅ Route to send WhatsApp messages
@app.post("/send-whatsapp/")
async def whatsapp_handler(
    file: UploadFile,
    message: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    file_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(send_bulk_whatsapp, file_path, message)
    return {"status": "WhatsApp sending started"}
