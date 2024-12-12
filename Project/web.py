from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import os
import json
import subprocess
import socket
from multiprocessing import Process

app = Flask(__name__, template_folder=os.path.expanduser('~/Project/Templates'))
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Paths for saving user and post data
USER_DATA_FILE = os.path.expanduser("~/Project/web_data/users/users.json")
POST_DATA_FILE = os.path.expanduser("~/Project/web_data/posts/posts.json")
CHAT_DATA_FILE = os.path.expanduser("~/Project/web_data/chats/chats.json")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_server():
    subprocess.Popen(['python3', 'server.py'], cwd=os.getcwd())

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

def run_server():                      # server.py를 실행하는 함수
    os.system('python server.py')


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

    users[username] = {"password": password, "major": major}
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
        "id": len(posts) + 1  # 게시글 ID
    }
    posts.insert(0, new_post)  # 최신 글을 맨 앞에 추가


    with open(POST_DATA_FILE, 'w') as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    flash("Post created successfully!")
    return redirect(url_for('get_posts'))


@app.route('/post/<int:post_id>', methods=['GET'])
def post_detail(post_id):
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        flash("Post not found!")
        return redirect(url_for('get_posts'))

    return render_template('post.html', post=post)

################################################################

@app.route('/chat/post/<int:post_id>', methods=['GET'])
def chat(post_id):
    if os.path.exists(POST_DATA_FILE):
        with open(POST_DATA_FILE, 'r') as f:
            posts = json.load(f)
    else:
        posts = []

    post = next((p for p in posts if p['id'] == post_id), None)
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


################################################################


if __name__ == "__main__":

    # Check if port is in use
    if is_port_in_use(8022):
        print("Port 8022 is already in use. Please free the port or use another port.")
        exit(1)

    # Ensure the directories exist
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(POST_DATA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CHAT_DATA_FILE), exist_ok=True)

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

    server_process = Process(target=run_server)
    server_process.start()

    app.run(host="0.0.0.0", port=5000, debug=True)

    server_process.join()


