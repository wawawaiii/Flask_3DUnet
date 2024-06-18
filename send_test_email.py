import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

def send_test_email():
    sender_email = "qhgud2563@gmail.com"
    receiver_email = os.getenv("RECEIVER_EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not receiver_email or not email_password:
        print('Email configuration is missing.')
        return

    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "Test Email from BrainGuard AI"

        body = "This is a test email."
        message.attach(MIMEText(body, "plain"))

        # Send the email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, email_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()

        print('Test email sent successfully.')
    except Exception as e:
        print(f'Failed to send test email. Error: {str(e)}')

send_test_email()
