import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, UploadFile, Form, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
import tempfile

router = APIRouter()

@router.post("/")
async def send_email_endpoint(
    file: UploadFile,
    subject: str = Form(...),
    body: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Logic to send email
    return {"status": "Emails are being sent"}

def send_bulk_email(file_path, subject, body, sender_email, sender_password):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = row['email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body.format(name=row['name']), 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, row['email'], msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Failed for {row['email']} - {e}")

@router.post("/send-emails/")
async def handle_bulk_email_upload(
    file: UploadFile,
    subject: str = Form(...),
    body: str = Form(...),
    sender_email: str = Form(...),
    sender_password: str = Form(...)
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        send_bulk_email(tmp_path, subject, body, sender_email, sender_password)
        return JSONResponse(content={"message": "Emails sent successfully"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
