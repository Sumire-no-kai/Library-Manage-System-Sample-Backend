import socket
import threading
import json
from handle import handle_client
from db import create_connection

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 16000))
    server.listen(5)
    print("Server started and listening on port 16000")

    connection = create_connection()

    while True:
        client_socket, client_address = server.accept()
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(
            target=handle_client,
            args=(client_socket, connection)
        )
        client_handler.start()


if __name__ == "__main__":
    start_server()
