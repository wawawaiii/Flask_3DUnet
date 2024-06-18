from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, send_from_directory, abort
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from firebase_admin import auth, storage, db
from werkzeug.utils import secure_filename
import os
import torch
import numpy as np
from models import UNet3d
from utils import load_nifti_image, save_nifti_image, predict, plot_prediction, plot_3d
import base64
from datetime import datetime
import csv
import io
import urllib.parse
from dotenv import load_dotenv

def init_routes(app, firebase_config):
    load_dotenv()  # 환경 변수 로드

    # 모델 로드
    model = UNet3d(4, 3, 24)
    model.load_state_dict(torch.load('C:/Users/HKIT/PycharmProjects/3DUnet/model/unet3d_state_dict.pth', map_location=torch.device('cpu')))
    model.eval()

    @app.route('/')
    def home():
        return render_template('login.html', firebase_config=firebase_config)

    @app.route('/login', methods=['POST'])
    def login():
        id_token = request.json.get('idToken')
        try:
            decoded_token = auth.verify_id_token(id_token)
            session['user'] = decoded_token['uid']
            session['user_email'] = decoded_token.get('email', '')
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            return jsonify({'status': 'failed', 'message': str(e)}), 401

    @app.route('/upload_files', methods=['POST'])
    def upload_files():
        if 'user' not in session:
            flash('You need to be logged in to upload files.')
            return redirect(url_for('home'))

        name = request.form.get('name')
        dob = request.form.get('dob')
        files = request.files.getlist('files')

        if len(files) != 4:
            session['error_message'] = 'NII 파일을 정확히 4개 선택하세요.'
            return redirect(url_for('index'))

        file_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_paths.append(file_path)

        # NII 파일 경로를 세션에 저장
        session['nii_files'] = ','.join(file_paths)
        session['name'] = name
        session['dob'] = dob

        flair_img = load_nifti_image(file_paths[0])
        t1_img = load_nifti_image(file_paths[1])
        t1ce_img = load_nifti_image(file_paths[2])
        t2_img = load_nifti_image(file_paths[3])

        images = np.stack([flair_img, t1_img, t1ce_img, t2_img])
        images = np.moveaxis(images, (0, 1, 2, 3), (0, 3, 2, 1))
        images_tensor = torch.tensor(images, dtype=torch.float32).unsqueeze(0)

        predictions = predict(model, images_tensor)

        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session['timestamp'] = timestamp

        # seg.nii 파일로 저장
        seg_output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'seg.nii')
        save_nifti_image(predictions.squeeze().cpu().numpy(), seg_output_path)

        img_base64 = plot_prediction(flair_img, predictions)
        session['img_data'] = img_base64

        # PNG 파일로 저장
        png_output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'segmentation.png')
        with open(png_output_path, "wb") as png_file:
            png_file.write(base64.b64decode(img_base64))

        # Firebase Storage에 이미지 업로드
        user_id = session['user']
        folder_path = f'{user_id}/{name}_{dob}_{timestamp}/'
        blob_name = f'{folder_path}segmentation.png'
        bucket = storage.bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(png_output_path)
        blob.make_public()

        # Firebase Realtime Database에 정보 저장
        db_key = f'{name}_{dob}_{timestamp}'
        db.reference(f'users/{user_id}/{db_key}').set({
            'name': name,
            'dob': dob,
            'image_url': blob.public_url,
            'timestamp': timestamp
        })

        return redirect(url_for('index'))

    @app.route('/feedback')
    def feedback():
        if 'user' in session:
            nii_files = session.get('nii_files', "")
            img_data = session.get('img_data', "")
            return render_template('feedback.html', nii_files=nii_files, img_data=img_data)
        else:
            flash('You need to be logged in to provide feedback.')
            return redirect(url_for('home'))

    @app.route('/send_feedback', methods=['POST'])
    def send_feedback():
        if 'user' not in session:
            flash('You need to be logged in to send feedback.')
            return redirect(url_for('home'))

        feedback = request.form.get('feedback')
        nii_files = request.form.get('nii_files').split(',')
        img_data = request.form.get('img_data')
        name = session.get('name')
        dob = session.get('dob')
        timestamp = session.get('timestamp')

        # 발신자 이메일을 고정된 이메일로 설정
        sender_email = "qhgud2563@gmail.com"
        user_email = session.get('user_email')
        user_id = session.get('user')
        receiver_email = os.getenv("RECEIVER_EMAIL")
        email_password = os.getenv("EMAIL_PASSWORD")

        if not sender_email or not receiver_email or not email_password:
            flash('Email configuration is missing.')
            return redirect(url_for('index'))

        print(f'Sending email from {sender_email} to {receiver_email} with password {email_password[:2]}********')

        try:
            # 파일 저장 경로
            folder_path = f'{user_id}/{name}_{dob}_{timestamp}/'

            # Firebase Storage에 파일 업로드 및 링크 생성
            file_urls = []
            bucket = storage.bucket()
            for file_path in nii_files:
                if file_path:  # Check if file_path is not empty
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        blob = bucket.blob(f'{folder_path}{filename}')
                        blob.upload_from_filename(file_path)
                        blob.make_public()
                        file_urls.append(blob.public_url)
                    else:
                        print(f'File not found: {file_path}')

            # segmentation.png 파일 링크 추가
            seg_blob = bucket.blob(f'{folder_path}segmentation.png')
            if seg_blob.exists():
                seg_blob.make_public()
                file_urls.append(seg_blob.public_url)

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = "Feedback on BrainGuard AI Model"

            body = f"Feedback from {user_email}:\n{feedback}\n\nDownload links:\n" + "\n".join(file_urls)
            message.attach(MIMEText(body, "plain"))

            # Send the email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, email_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()

            flash('Feedback sent successfully.')
        except Exception as e:
            flash(f'Failed to send feedback. Error: {str(e)}')
            print(f'Error: {str(e)}')  # 에러 로그 출력

        return redirect(url_for('index'))

    @app.route('/index')
    def index():
        if 'user' in session:
            img_data = session.pop('img_data', None)
            nii_img_data = session.pop('nii_img_data', None)
            error_message = session.pop('error_message', None)
            return render_template('index.html', img_data=img_data, nii_img_data=nii_img_data, error_message=error_message)
        else:
            flash('You need to be logged in to access this page.')
            return redirect(url_for('home'))

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        flash('You have been logged out.')
        return redirect(url_for('home'))

    @app.route('/upload_nii', methods=['POST'])
    def upload_nii():
        if 'user' not in session:
            flash('You need to be logged in to upload files.')
            return redirect(url_for('home'))

        nii_file = request.files.get('nii_file')

        if not nii_file:
            session['error_message'] = 'NII 파일을 선택하세요.'
            return redirect(url_for('index'))

        filename = secure_filename(nii_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        nii_file.save(file_path)

        nii_img = load_nifti_image(file_path)
        nii_img_base64 = plot_nii_image(nii_img)
        session['nii_img_data'] = nii_img_base64

        return redirect(url_for('index'))

    @app.route('/download/<filename>')
    def download_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

    @app.route('/patient_info')
    def patient_info():
        if 'user' in session:
            return render_template('patient_info.html')
        else:
            flash('You need to be logged in to access this page.')
            return redirect(url_for('home'))

    @app.route('/search_patient', methods=['GET'])
    def search_patient():
        if 'user' not in session:
            return jsonify([])

        query = request.args.get('query', '').strip()
        if not query:
            return jsonify([])

        user_id = session['user']
        patients_ref = db.reference(f'users/{user_id}')
        all_patients = patients_ref.get()

        if not all_patients:
            return jsonify([])

        matched_keys = [key for key in all_patients.keys() if query.lower() in key.lower()]
        matched_keys.sort(reverse=True)  # 최신 데이터를 먼저 표시

        unique_patients = {}
        for key in matched_keys:
            name_dob = '_'.join(key.split('_')[:2])
            if name_dob not in unique_patients:
                unique_patients[name_dob] = []
            unique_patients[name_dob].append(key)

        results = [{'name_dob': name_dob, 'keys': keys} for name_dob, keys in unique_patients.items()]

        return jsonify(results)

    @app.route('/load_patient_info', methods=['GET'])
    def load_patient_info():
        if 'user' not in session:
            return jsonify({})

        keys = request.args.getlist('keys')
        page = int(request.args.get('page', 1))
        per_page = 1
        if not keys:
            return jsonify({})

        start = (page - 1) * per_page
        end = start + per_page
        paginated_keys = keys[start:end]

        user_id = session['user']
        patient_data_list = []
        for key in paginated_keys:
            patient_data = db.reference(f'users/{user_id}/{key}').get()
            if patient_data:
                patient_data['db_key'] = key
                patient_data_list.append(patient_data)

        return jsonify({
            'patient_data': patient_data_list,
            'total': len(keys),
            'page': page,
            'per_page': per_page
        })

    @app.route('/save_patient_info', methods=['POST'])
    def save_patient_info():
        if 'user' not in session:
            flash('You need to be logged in to save patient information.')
            return redirect(url_for('home'))

        user_id = session['user']
        db_key = request.form.get('db_key')
        if not db_key:
            flash('Invalid patient data.')
            return redirect(url_for('patient_info'))

        patient_info = {
            'name': request.form.get('name'),
            'dob': request.form.get('dob'),
            'gender': request.form.get('gender'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'address': request.form.get('address'),
            'diagnosis': request.form.get('diagnosis'),
            'medical_history': request.form.get('medical_history'),
            'treatment_plan': request.form.get('treatment_plan'),
            'allergies': request.form.get('allergies'),
            'insurance_info': request.form.get('insurance_info'),
            'scan_date': request.form.get('scan_date'),
            'segmentation_result': request.form.get('segmentation_result')
        }

        db.reference(f'users/{user_id}/{db_key}').update(patient_info)

        flash('Patient information saved successfully.')
        return redirect(url_for('patient_info'))

    @app.route('/delete_patient_info', methods=['DELETE'])
    def delete_patient_info():
        if 'user' not in session:
            return jsonify({'status': 'failed', 'message': 'You need to be logged in to delete patient information.'})

        db_key = request.args.get('db_key')
        if not db_key:
            return jsonify({'status': 'failed', 'message': 'Invalid patient data.'})

        user_id = session['user']
        db.reference(f'users/{user_id}/{db_key}').delete()

        return jsonify({'status': 'success'})

    @app.route('/export_patient_info', methods=['GET'])
    def export_patient_info():
        if 'user' not in session:
            flash('You need to be logged in to export patient information.')
            return redirect(url_for('home'))

        keys = request.args.getlist('keys')
        if not keys:
            flash('No patient data available to export.')
            return redirect(url_for('patient_info'))

        user_id = session['user']
        patients_ref = db.reference(f'users/{user_id}')
        data_to_export = {key: patients_ref.child(key).get() for key in keys}

        output = io.StringIO()
        writer = csv.writer(output)
        header = ['name', 'dob', 'gender', 'phone', 'email', 'address', 'diagnosis', 'medical_history', 'treatment_plan', 'allergies', 'insurance_info', 'scan_date', 'segmentation_result', 'image_url', 'timestamp']
        writer.writerow(header)
        for key, value in data_to_export.items():
            row = [value.get(col, '') for col in header]
            writer.writerow(row)

        output.seek(0)
        if data_to_export:
            first_patient = list(data_to_export.values())[0]
            filename = f"{first_patient['name']}_{first_patient['dob']}.csv"
        else:
            filename = f"patient_info_{datetime.now().strftime('%Y%m%d')}.csv"

        encoded_filename = urllib.parse.quote(filename)

        response = Response(output, mimetype='text/csv')
        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.data = '\ufeff'.encode('utf-8') + output.getvalue().encode('utf-8')  # BOM 추가 및 UTF-8 인코딩

        return response

    @app.route('/report_generation')
    def report_generation():
        if 'user' in session:
            return render_template('report_generation.html')
        else:
            flash('You need to be logged in to access this page.')
            return redirect(url_for('home'))

    @app.route('/get_patient_info', methods=['GET'])
    def get_patient_info():
        if 'user' not in session:
            return jsonify({})

        user_id = session['user']
        patient_data = db.reference(f'users/{user_id}').order_by_key().limit_to_last(1).get()
        patient_info = {}
        if patient_data:
            for key, value in patient_data.items():
                patient_info = value
                patient_info['name'] = value.get('name', '')
                patient_info['scan_date'] = value.get('scan_date', '')
                patient_info['img_data'] = session.get('img_data', '')

        return jsonify(patient_info)

def plot_nii_image(nii_img):
    import matplotlib.pyplot as plt
    from skimage.util import montage
    import numpy as np
    import io
    import base64

    if nii_img.ndim == 4:
        nii_img = nii_img[:, :, :, 0]

    if nii_img.ndim != 3:
        raise ValueError("Input array has to be 3-dimensional for grayscale images.")

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.imshow(np.rot90(montage(nii_img)), cmap='bone')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    img_bytes = buf.read()
    img_base64 = base64.b64encode(img_bytes).decode('ascii')
    return img_base64
