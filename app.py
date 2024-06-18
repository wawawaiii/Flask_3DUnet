from flask import Flask
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, auth, storage, db

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# 환경 변수에서 Firebase 설정 정보를 가져옵니다.
firebase_config = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID'),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
}

# Firebase Admin 초기화
cred = credentials.Certificate('C:/Users/HKIT/PycharmProjects/3DUnet/brain-tumor-2ea99-firebase-adminsdk-9qkk0-59a28bcf07.json')  # Firebase Admin SDK JSON 파일 경로
firebase_admin.initialize_app(cred, {
    'storageBucket': firebase_config['storageBucket'],
    'databaseURL': firebase_config['databaseURL']
})

app = Flask(__name__)
CORS(app)  # CORS 설정 추가
app.secret_key = os.urandom(24)  # 세션을 위한 고유하고 비밀스러운 키 설정
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Flask-Session 설정
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

from routes import init_routes
init_routes(app, firebase_config)

if __name__ == '__main__':
    app.run(debug=True)
