from flask import Flask, request, render_template_string, session, redirect, url_for
from cryptography.fernet import Fernet

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'your_flask_secret_key'  # 세션 암호화용 키

# ✅ 암호화 키 설정 (1회만 생성하고 안전한 곳에 보관)
# key = Fernet.generate_key()
# print(key)
key = b'your_fernet_key_here'  # 실제 생성된 키를 여기에 넣으세요
cipher = Fernet(key)

# ✅ AI 생성물 탐지 함수
def is_ai_generated(text):
    ai_patterns = ["기계", "인공지능", "모델", "딥러닝", "확률"]
    return any(pattern in text for pattern in ai_patterns)

# ✅ 디지털 워터마크 삽입 함수
def insert_watermark(text):
    invisible_watermark = "\u200B\u200C\u200D"  # zero-width characters
    return text + invisible_watermark

# ✅ 콘텐츠 암호화/복호화 함수
def encrypt_content(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt_content(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()

# ✅ HTML 템플릿
HTML_TEMPLATE = '''
<!doctype html>
<html>
<head><title>AI 콘텐츠 보안 시스템</title></head>
<body>
  <h2>콘텐츠 보호 시스템</h2>

  {% if not session.get('logged_in') %}
    <form method="post">
      <input type="password" name="password" placeholder="비밀번호 입력"><br>
      <input type="submit" value="로그인">
    </form>
    <p style="color:red">{{ message }}</p>

  {% else %}
    <form method="post">
      <textarea name="content" rows="5" cols="50" placeholder="콘텐츠 입력..."></textarea><br>
      <input type="submit" name="check" value="AI 판별 및 보호 적용">
    </form>

    {% if result %}
      <p><strong>결과:</strong> {{ result }}</p>
      <p><strong>암호화된 콘텐츠:</strong> {{ encrypted }}</p>
      <p><strong>복호화된 원본:</strong> {{ decrypted }}</p>
    {% endif %}

    <a href="{{ url_for('logout') }}">로그아웃</a>
  {% endif %}
</body>
</html>
'''

# ✅ 메인 라우트
@app.route('/', methods=['GET', 'POST'])
def index():
    message, result, encrypted, decrypted = '', '', '', ''

    if request.method == 'POST':
        if not session.get('logged_in'):
            user_pw = request.form.get('password')
            if user_pw == 'secure123':  # 설정한 접근 암호
                session['logged_in'] = True
                return redirect(url_for('index'))
            else:
                message = "비밀번호가 틀렸습니다."
        else:
            content = request.form.get('content')
            if content:
                if is_ai_generated(content):
                    result = "AI 생성물로 감지됨. 워터마크 및 암호화 적용 완료."
                    watermarked = insert_watermark(content)
                    encrypted = encrypt_content(watermarked)
                    decrypted = decrypt_content(encrypted)  # 복호화 예시 표시
                else:
                    result = "사람이 작성한 콘텐츠입니다. 암호화만 적용합니다."
                    encrypted = encrypt_content(content)
                    decrypted = decrypt_content(encrypted)

    return render_template_string(
        HTML_TEMPLATE,
        message=message,
        result=result,
        encrypted=encrypted,
        decrypted=decrypted
    )

# ✅ 로그아웃 기능
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# ✅ 서버 실행
if __name__ == '__main__':
    app.run(debug=True)
