import asyncio
import websockets
import json
import os

# Paths for saving chat data
CHAT_DATA_FILE = os.path.expanduser("~/Project/web_data/chats/chats.json")
USER_DATA_FILE = os.path.expanduser("~/Project/web_data/users/users.json")

# 채팅 방 관리: {room_id: {"buyer": WebSocket, "seller": WebSocket}}
chat_rooms = {}

def load_user_data():
    """
    Load user data from JSON file.
    """
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_chat_data():
    """
    Load chat data from JSON file.
    """
    if os.path.exists(CHAT_DATA_FILE):
        with open(CHAT_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_chat_data(data):
    """
    Save chat data to JSON file.
    """
    with open(CHAT_DATA_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def chat_handler(websocket, path):
    """
    Handle WebSocket connection.
    """
    try:
        # 클라이언트로부터 초기 데이터 수신
        initial_data = await websocket.recv()
        client_data = json.loads(initial_data)
        post_id = client_data.get("post_id")
        role = client_data.get("role")
        user_id = client_data.get("user_id")  # 클라이언트에서 전달된 user_id

        print(f"Received connection: Post ID={post_id}, Role={role}, User ID={user_id}")

        # 입력 데이터 검증
        if not post_id or not role or not user_id:
            await websocket.send(json.dumps({"error": "필수 데이터가 누락되었습니다."}))
            return
        
        # room_id 생성 (post_id와 user_id 결합)
        room_id = f"{post_id}_{user_id}"

        # 새로운 채팅 방 생성 또는 기존 방에 연결
        if room_id not in chat_rooms:
            chat_rooms[room_id] = {"buyer": None, "seller": None}

        # 역할 설정 및 WebSocket 연결
        if role == "buyer":
            chat_rooms[room_id]["buyer"] = websocket
        elif role == "seller":
            chat_rooms[room_id]["seller"] = websocket
        else:
            await websocket.send(json.dumps({"error": "잘못된 역할"}))
            return

        # 채팅 로그 초기화 또는 로드
        chat_data = load_chat_data()
        if room_id not in chat_data:
            chat_data[room_id] = [] #chats.json에 room_id 생성
        save_chat_data(chat_data)

        # 연결 성공 메시지 전송
        await websocket.send(json.dumps({"message": f"Connected as {role} in room {room_id}"}))

        # 메시지 수신 및 전송
        while True:
            message = await websocket.recv()
            chat_data[room_id].append({"role": role, "message": message})
            save_chat_data(chat_data)
            await broadcast_message(room_id, role, message)

    except websockets.ConnectionClosed:
        print("WebSocket 연결 종료")
        if room_id in chat_rooms:
            chat_rooms[room_id][role] = None
            # 방이 비어 있으면 삭제
            if not chat_rooms[room_id]["buyer"] and not chat_rooms[room_id]["seller"]:
                del chat_rooms[room_id]
        save_chat_data(chat_data) #연결 종료 시 데이터 저장
        print(f"{role} disconnected from room {room_id}.")

async def broadcast_message(room_id, sender_role, message):
    """
    상대방 클라이언트로 메시지 전송.
    """
    if room_id not in chat_rooms:
        chat_rooms[room_id] = {"buyer" : None, "seller" : None} #메모리에 room_id 초기화
        return

    recipient_role = "seller" if sender_role == "buyer" else "buyer"
    recipient_socket = chat_rooms[room_id][recipient_role]

    if recipient_socket:
        await recipient_socket.send(json.dumps({"role": sender_role, "message": message}))

async def main():
    """
    Start the WebSocket server.
    """
    server = await websockets.serve(chat_handler, "0.0.0.0", 8888)
    print("WebSocket 서버가 8888 포트에서 실행 중입니다.")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("서버가 종료되었습니다.")



