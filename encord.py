import base64

# 폰트 파일 경로
font_path = 'malgunbd.ttf'  # 예: C:\path\to\malgun.ttf

# Base64로 인코딩
with open(font_path, 'rb') as font_file:
    font_data = font_file.read()
    encoded_font = base64.b64encode(font_data).decode('utf-8')

# 결과 출력 또는 파일에 저장
print(encoded_font)
