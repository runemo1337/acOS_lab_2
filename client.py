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

    def await_response(self):
        "Состояние 2: Ожидание ответа"
        try:
            self.socket.sendall(self.current_request.encode('utf-8'))
            print("Запрос отправлен")
            self.state = 'READ_RESPONSE'
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            self.state = 'ERROR_HANDLING'
    
    def read_response(self):
        "Состояние 3: Чтение ответа"
        try:
            response = self.socket.recv(1024).decode('utf-8')
            if response:
                self.server_response = response
                print(f"Получен ответ: '{self.server_response}'")
                self.state = 'CREATE_REQUEST'
                time.sleep(2)
            else:
                print("Сервер закрыл соединение")
                self.state = 'ERROR_HANDLING'
                
        except socket.timeout:
            print("Таймаут ожидания ответа")
            self.state = 'ERROR_HANDLING'
        except Exception as e:
            print(f"Ошибка чтения: {e}")
            self.state = 'ERROR_HANDLING'