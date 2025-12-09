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
            self.socket.connect(('localhost', 12345))
            print("Соединение с сервером установлено")
            return True
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            self.state = 'ERROR_HANDLING'
            return False
    
    def create_request(self):
        self.current_request = input("Введите запрос для сервера: ").strip()
        if self.current_request.lower() == 'exit':
            print(" Завершение работы...")
            self.work = False
            return
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


    def handle_error(self):
        """Состояние 4: Обработка ошибки"""
        print("[ERROR_HANDLING] Обработка ошибки...")
        if self.socket:
            self.socket.close()
            self.socket = None
        
        time.sleep(3)
        print("Попытка переподключения...")
        if self.connect_to_server():
            self.state = 'CREATE_REQUEST'
        else:
            print("Не удалось восстановить соединение")
            time.sleep(5)


    def run(self):
        """Основной цикл клиента"""
        print("Клиент запущен")
        
        if not self.connect_to_server():
            return
        
        while True:
            try:
                if self.state == 'CREATE_REQUEST':
                    self.create_request()
                elif self.state == 'AWAIT_RESPONSE':
                    self.await_response()
                elif self.state == 'READ_RESPONSE':
                    self.read_response()
                elif self.state == 'ERROR_HANDLING':
                    self.handle_error()
                
                if not self.work:
                    print("Завершение работы клиента")
                    if self.socket:
                        self.socket.close()
                    break
                    
            except KeyboardInterrupt:
                print("\nКлиент остановлен по запросу пользователя")
                if self.socket:
                    self.socket.close()

                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                self.state = 'ERROR_HANDLING'



if __name__ == "__main__":
    client = ClientStateMachine()
    client.run()