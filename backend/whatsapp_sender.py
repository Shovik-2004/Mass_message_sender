import pandas as pd
import time
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from fastapi import APIRouter, BackgroundTasks, UploadFile, Form
from tempfile import NamedTemporaryFile

router = APIRouter()

@router.post("/")
async def send_whatsapp_endpoint(
    file: UploadFile,
    message: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Save uploaded file temporarily
    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    background_tasks.add_task(send_bulk_whatsapp, tmp_path, message)
    return {"status": "WhatsApp messages are being sent in the background."}

def send_bulk_whatsapp(file_path, message):
    try:
        df = pd.read_excel(file_path)

        # Setup Chrome driver
        chrome_service = Service("/opt/homebrew/bin/chromedriver")
        driver = webdriver.Chrome(service=chrome_service)
        driver.get("https://web.whatsapp.com")

        input("🔒 Scan the QR code on WhatsApp Web and press Enter here...")

        for _, row in df.iterrows():
            try:
                phone = str(row['phone']).strip().replace(" ", "").replace("+", "")
                url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
                driver.get(url)
                time.sleep(10)  # Let the chat window load

                send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                send_btn.click()
                print(f"✅ Sent to {phone}")
                time.sleep(5)
            except Exception as e:
                print(f"❌ Failed for {phone}: {e}")
    finally:
        driver.quit()
        os.remove(file_path)
