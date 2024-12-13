from flask import Flask, session, request, render_template, redirect, url_for, flash, jsonify
import os
import json
import subprocess
import socket
from multiprocessing import Process

from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder=os.path.expanduser('~/Project/Templates'))
app.secret_key = 'your_secret_key'  # Required for flashing messages



# Paths for saving user and post data
USER_DATA_FILE = os.path.expanduser("~/Project/web_data/users/users.json")
POST_DATA_FILE = os.path.expanduser("~/Project/web_data/posts/posts.json")
CHAT_DATA_FILE = os.path.expanduser("~/Project/web_data/chats/chats.json")

##################################################################

# 이미지 업로드를 위한 폴더 경로
UPLOAD_FOLDER = os.path.expanduser("~/Project/static/uploads")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 이미지 파일 확장자 제한
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 파일 확장자 확인 함수
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

##################################################################

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def terminate_process_on_port(port):
    """특정 포트를 사용하는 프로세스를 종료합니다."""
    try:
        result = subprocess.check_output(f"lsof -ti:{port}", shell=True).decode().strip()
        if result:
            subprocess.check_call(f"kill -9 {result}", shell=True)
            print(f"{port} 포트를 사용하는 프로세스를 종료했습니다.")
    except subprocess.CalledProcessError:
        print(f"{port} 포트를 사용하는 프로세스가 없습니다.")

def run_server():
    """server.py WebSocket 서버를 실행합니다."""
    if is_port_in_use(8888):
        print("8888 포트가 이미 사용 중입니다. 프로세스를 종료합니다...")
        terminate_process_on_port(8888)

    try:
        process = subprocess.Popen(['python3', 'server.py'], cwd=os.getcwd())
        print(f"server.py가 PID {process.pid}로 시작되었습니다.")
    except Exception as e:
        print(f"server.py를 시작하지 못했습니다: {e}")

##################################################################

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_chat_data():
    try:
        with open(CHAT_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def save_chat_data(data):
    with open(CHAT_DATA_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup_page', methods=['GET'])
def signup_page():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    major = request.form['major']

    if len(password) < 8:
        flash("Password must be at least 8 characters long.")
        return redirect(url_for('signup_page'))
    if not any(char.isdigit() for char in password):
        flash("Password must contain at least one number.")
        return redirect(url_for('signup_page'))
    if not any(char.isalpha() for char in password):
        flash("Password must contain at least one letter.")
        return redirect(url_for('signup_page'))
    if password != confirm_password:
        flash("Passwords do not match!")
        return redirect(url_for('signup_page'))
    
    users = load_user_data()
    if username in users:
        flash("Username already exists!")
        return redirect(url_for('signup_page'))

    users[username] = {"user_id": username, "password": password, "major": major}
    save_user_data(users)
    flash("Registration successful! You can now log in.")
    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    users = load_user_data()

    if username in users and users[username]['password'] == password:
        return redirect(url_for('get_posts'))  # Redirect to market page
    else:
        flash('Invalid username or password.')
        return redirect(url_for('home'))

@app.route('/get_posts', methods=['GET'])
def get_posts():
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    return render_template('market.html', posts=posts)


@app.route('/create_post_page', methods=['GET'])
def create_post_page():
    return render_template('create.html')


@app.route('/create_post', methods=['POST'])
def create_post():
    # 입력 데이터 받기
    user_id = request.form.get('user_id')
    title = request.form.get('title')
    content1 = request.form.get('content1')  # 책 제목
    content2 = request.form.get('content2')  # 가격
    content3 = request.form.get('content3')  # 책 상태
    content4 = request.form.get('content4')  # 위치

    ####################################################################

    # 이미지 처리
    image = request.files.get('image')  # 파일 가져오기
    image_filename = "default.png"  # 기본 이미지 파일명 설정
    if image and allowed_file(image.filename):
        # 이미지 파일명 안전하게 처리
        image_filename = secure_filename(image.filename)
        # 이미지 저장
        try:
            image.save(os.path.join(UPLOAD_FOLDER, image_filename))
        except Exception as e:
            print(f"이미지 저장 실패: {e}")
            flash("이미지를 저장하는 데 문제가 발생했습니다.")
            return redirect(url_for('create_post_page'))

    ####################################################################


    if not user_id or not title or not content1 or not content2 or not content3 or not content4:
        flash("All fields are required!")
        return redirect(url_for('create_post_page'))

    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    # 새 게시글 추가
    new_post = {
        "user_id": user_id,
        "title": title,
        "content1": content1,
        "content2": content2,
        "content3": content3,
        "content4": content4,
        "image": image_filename,  ######################################## 이미지 파일명 추가
        "post_id": len(posts) + 1  # 게시글 ID
    }
    posts.insert(0, new_post)  # 최신 글을 맨 앞에 추가


    with open(POST_DATA_FILE, 'w') as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    flash("Post created successfully!")
    return redirect(url_for('get_posts'))

@app.route('/posts', methods=['GET'])
def posts():
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    return render_template('market.html', posts=posts)

@app.route('/post/<int:post_id>', methods=['GET'])
def post_detail(post_id):
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    post = next((p for p in posts if p['post_id'] == post_id), None)
    if not post:
        flash("Post not found!")
        return redirect(url_for('get_posts'))

    return render_template('post.html', post=post)


@app.route('/buy/<int:post_id>', methods=['GET'])
def buy_post(post_id):
    # id가 유효한지 확인
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    post = next((p for p in posts if p['post_id'] == post_id), None)
    if not post:
        flash("게시글을 찾을 수 없습니다!")
        return redirect(url_for('get_posts'))

    # 해당 id를 사용하여 채팅 페이지로 리다이렉트
    return redirect(url_for('chat', post_id=post_id))


@app.route('/chat/post/<int:post_id>', methods=['GET'])
def chat(post_id):
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    post = next((p for p in posts if p['post_id'] == post_id), None)
    if not post:
        flash("Post not found!")
        return redirect(url_for('get_posts'))

    return render_template('chat.html', post=post)

@app.route('/chat/room/<room_id>', methods=['GET', 'POST'])
def chat_room(room_id):
    """채팅방 생성 및 채팅 메시지 처리"""
    chat_data = load_chat_data()

    if request.method == 'POST':
        sender_id = request.form.get('sender_id')
        message = request.form.get('message')

        if not sender_id or not message:
            return jsonify({"error": "sender_id와 message는 필수입니다."}), 400

        if room_id not in chat_data:
            chat_data[room_id] = []

        chat_data[room_id].append({"sender_id": sender_id, "message": message})
        save_chat_data(chat_data)

        return jsonify({"success": True, "message": "Message sent.", "messages": chat_data[room_id]}), 200

    return render_template('chat.html', room_id=room_id, messages=chat_data.get(room_id, []))

@app.route('/create_room', methods=['POST'])
def create_room():
    """사용자 ID와 게시글 ID로 roomID 생성"""
    user_id = request.form.get('user_id')
    post_id = request.form.get('post_id')

    if not user_id or not post_id:
        return jsonify({"error": "user_id와 post_id가 필요합니다."}), 400

    if not user_id.isalnum() or not post_id.isdigit():
        return jsonify({"error": "user_id는 영문/숫자 조합이어야 하며, post_id는 숫자여야 합니다."}), 400

    room_id = f"{user_id}_{post_id}"
    return redirect(url_for('chat_room', room_id=room_id))

#####################################################################################

#if is_port_in_use(5000):
        #print("5000번 포트가 이미 사용 중입니다. 프로세스를 종료합니다...")
        #terminate_process_on_port(5000)

#####################################################################################

if __name__ == "__main__":

    # Ensure the directories exist
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(POST_DATA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CHAT_DATA_FILE), exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Ensure the data files exist
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    if not os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'w') as f:
            json.dump([], f)

    if not os.path.exists(CHAT_DATA_FILE):
        with open(CHAT_DATA_FILE, 'w') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    
    ###################################################################
    # Ensure the upload folder contains a placeholder file
    placeholder_file = os.path.join(UPLOAD_FOLDER, ".placeholder")
    if not os.path.exists(placeholder_file):
        with open(placeholder_file, "w") as f:
            f.write("")
    ###################################################################

    server_process = Process(target=run_server)
    server_process.start()

    # Run Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)

    server_process.join()



