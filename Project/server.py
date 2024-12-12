import asyncio
import websockets

# 채팅방을 관리하는 딕셔너리: 채팅방 ID -> 사용자 목록
chat_rooms = {}

async def handle_connection(websocket, path):
    # 클라이언트가 보내는 데이터 처리 (여기선 역할 정보 수신)
    try:
        # 클라이언트가 처음 연결될 때 역할을 설정합니다.
        role = await websocket.recv()  # 클라이언트가 보낸 역할 (구매자 또는 판매자)
        print(f"새로운 연결! 역할: {role}")

        # 연결된 클라이언트를 적절한 채팅방에 배정합니다.
        if role == "buyer":
            room_id = "chat_room"  # 예시로 하나의 채팅방을 사용
        elif role == "seller":
            room_id = "chat_room"
        else:
            await websocket.send("잘못된 역할입니다. 종료합니다.")
            return

        # 채팅방에 클라이언트를 추가합니다.
        if room_id not in chat_rooms:
            chat_rooms[room_id] = {"buyer": None, "seller": None}

        if role == "buyer":
            chat_rooms[room_id]["buyer"] = websocket
        elif role == "seller":
            chat_rooms[room_id]["seller"] = websocket

        # 클라이언트에게 채팅방에 입장했다고 알려줍니다.
        await websocket.send(f"{role}로 채팅방에 입장하셨습니다.")

        # 채팅 메시지를 기다리며, 연결을 유지합니다.
        while True:
            message = await websocket.recv()  # 클라이언트로부터 메시지를 받음
            print(f"받은 메시지: {message}")

            # 같은 채팅방에 연결된 다른 클라이언트에게 메시지를 전달합니다.
            if role == "buyer" and chat_rooms[room_id]["seller"]:
                await chat_rooms[room_id]["seller"].send(f"구매자: {message}")
            elif role == "seller" and chat_rooms[room_id]["buyer"]:
                await chat_rooms[room_id]["buyer"].send(f"판매자: {message}")
                
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        # 연결 종료 시 처리
        if room_id in chat_rooms:
            if role == "buyer":
                chat_rooms[room_id]["buyer"] = None
            elif role == "seller":
                chat_rooms[room_id]["seller"] = None
        print(f"{role} 연결 종료.")

# 서버 실행
async def main():
    server = await websockets.serve(handle_connection, "0.0.0.0", 8888)
    print("WebSocket 서버가 실행 중입니다...")
    await server.wait_closed()

# 이벤트 루프 실행
asyncio.run(main())
