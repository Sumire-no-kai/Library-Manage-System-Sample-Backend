import json
import base64
import hashlib
import struct
from db import check_login, register_user, get_books, insert_book, delete_book, borrow_book, return_book


def handle_client(client_socket, connection):
    with client_socket:
        # Perform WebSocket handshake
        request = client_socket.recv(1024).decode('utf-8')
        headers = parse_headers(request)

        if 'Sec-WebSocket-Key' in headers:
            websocket_handshake(client_socket, headers['Sec-WebSocket-Key'])
            while True:
                message = receive_message(client_socket)
                if message:
                    print(f"Received message: {message}")  # Debugging line
                    try:
                        request_data = json.loads(message)
                        response = handle_request(connection, request_data)
                        send_message(client_socket, json.dumps(response))
                    except json.JSONDecodeError:
                        response = {"action": "error", "message": "Invalid JSON"}
                        send_message(client_socket, json.dumps(response))
                else:
                    break


def parse_headers(request):
    headers = {}
    lines = request.split("\r\n")
    for line in lines[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key] = value
    return headers


def websocket_handshake(client_socket, websocket_key):
    accept_key = base64.b64encode(
        hashlib.sha1((websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
    handshake_response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key}\r\n"
        "\r\n"
    )
    client_socket.send(handshake_response.encode('utf-8'))
    print("WebSocket handshake successful")  # Debugging line


def receive_message(client_socket):
    try:
        data = client_socket.recv(2)
        if not data:
            return None

        # Check if this is a text frame (opcode 0x1)
        opcode = data[0] & 0x0F
        if opcode == 0x8:
            print("Connection closed by the client")
            return None
        elif opcode != 0x1:
            print(f"Received non-text frame: opcode {opcode}")
            return None

        # Get the payload length
        payload_length = data[1] & 0x7F
        if payload_length == 126:
            data = client_socket.recv(2)
            payload_length = struct.unpack(">H", data)[0]
        elif payload_length == 127:
            data = client_socket.recv(8)
            payload_length = struct.unpack(">Q", data)[0]

        # Get the masking key
        masking_key = client_socket.recv(4)

        # Get the masked payload
        masked_payload = client_socket.recv(payload_length)

        # Unmask the payload
        payload = bytearray([masked_payload[i] ^ masking_key[i % 4] for i in range(payload_length)])
        return payload.decode('utf-8')
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def send_message(client_socket, message):
    message = message.encode('utf-8')
    message_len = len(message)
    header = b'\x81'
    if message_len <= 125:
        header += struct.pack('B', message_len)
    elif message_len >= 126 and message_len <= 65535:
        header += struct.pack('!BH', 126, message_len)
    else:
        header += struct.pack('!BQ', 127, message_len)
    client_socket.send(header + message)


def handle_request(connection, request_data):
    action = request_data.get("action")

    if action == "login":
        username = request_data.get("username")
        password = request_data.get("password")
        result = check_login(connection, username, password)
        success = result["success"]
        user_id = result["user_id"]
        response = {"action": "login", "success": success, "user_id": user_id}
    elif action == "register":
        username = request_data.get("username")
        password = request_data.get("password")
        success = register_user(connection, username, password)
        response = {"action": "register", "success": success}
    elif action == "get_books":
        books = get_books(connection)
        response = {"action": "get_books", "books": books}
    elif action == "insert_book":
        title = request_data.get("title")
        author = request_data.get("author")
        publication_year = request_data.get("publication_year")
        publisher = request_data.get("publisher")
        entry_date = request_data.get("entry_date")
        success = insert_book(connection, title, author, publication_year, publisher, entry_date)
        response = {"action": "insert_book", "success": success}
    elif action == "delete_book":
        book_id = request_data.get("book_id")
        print("Receiverd the book ID is: " + str(book_id))
        success = delete_book(connection, book_id)
        response = {"action": "delete_book", "success": success}
    elif action == "borrow_book":
        book_id = request_data.get("book_id")
        user_id = request_data.get("user_id")
        success = borrow_book(connection, book_id, user_id)
        response = {"action": "borrow_book", "success": success}
    elif action == "return_book":
        book_id = request_data.get("book_id")
        success = return_book(connection, book_id)
        response = {"action": "return_book", "success": success}
    else:
        response = {"action": "error", "message": "Unknown action"}

    print(f"Sending response: {response}")  # Debugging line
    return response
