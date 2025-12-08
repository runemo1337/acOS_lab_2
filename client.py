import socket
import time
import random


class ClientStateMachine:
    def __init__(self):
        self.state = 'CREATE_REQUEST'
        self.socket = None
        self.current_request = None
        self.server_response = None

    def connect_to_server(self):
        "Установливаем соединение с сервером"
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect(('localhost', 8888))
            print("Соединение с сервером установлено")
            return True
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            self.state = 'ERROR_HANDLING'
            return False
    
    def create_request(self):
        "Состояние 1: Создание запроса"
        requests = [
            "Hello Server",
            "Test message",
            "Ping",
            "Any data",
            "Request from client"
        ]
        
        self.current_request = random.choice(requests)
        print(f"Отправляем: '{self.current_request}'")
        self.state = 'AWAIT_RESPONSE'