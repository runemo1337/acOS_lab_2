import socket
import time
import random


class Client_COMPANY_NAME:
    def __init__(self):
        self.current_state = 'create_request'
        self.socket = None
        self.current_request = None
        self.server_answer = None
        self.work = True
        self.encoder = 'utf-8'

    def start_work_client(self,
                          host='localhost',
                          port=12345,
                          client_timeout=10.0):


        while self.work:
            try:
                self.run_state_machine()
            except KeyboardInterrupt:
                print("\n Клиент остановлен")
                self.work = False
                break
            except Exception as e:
                print(f" Ошибка клиента: {e}")
                self.current_state = 'catch_error'

        self.cleanup()

    def run_state_machine(self):
        """Конечный автомат клиента"""
        if self.current_state == 'create_request':
            self.create_request_func()
        elif self.current_state == 'await_answer':
            self.send_and_wait()
        elif self.current_state == 'read_answer':
            self.read_answer_func()
        elif self.current_state == 'catch_error':
            self.editing_error()

    def create_request_func(self):



        self.current_request = input("Введите запрос для сервера: ").strip()


        if self.current_request.lower() == 'exit':
            print(" Завершение работы...")
            self.work = False
            return


        print(f"Создан запрос: '{self.current_request}'")
        self.current_state = 'await_answer'

    def send_and_wait(self):

        try:
            if not self.socket:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10.0)
                self.socket.connect(('localhost', 12345))
                print(" Подключение к серверу установлено")

            # Отправляем запрос
            self.socket.sendall(self.current_request.encode(self.encoder))
            print(f" Отправлен запрос: '{self.current_request}', жду ответ...")
            self.current_state = 'read_answer'

        except Exception as e:
            print(f" Ошибка отправки: {e}")
            self.current_state = 'catch_error'

    def read_answer_func(self):

        try:
            answer = self.socket.recv(1024).decode(self.encoder)
            if answer:
                self.server_answer = answer
                print(f"Получен ответ: '{self.server_answer}'")
                self.current_state = 'create_request'
            else:
                print(" Сервер закрыл соединение")
                self.socket.close()
                self.socket = None
                self.current_state = 'catch_error'

        except socket.timeout:
            print(" Таймаут ожидания ответа")
            self.current_state = 'catch_error'
        except Exception as e:
            print(f" Ошибка чтения: {e}")
            self.current_state = 'catch_error'

    def editing_error(self):

        print(" Обработка ошибки клиента...")

        if self.socket:
            self.socket.close()
            self.socket = None

        time.sleep(3)
        print(" Попытка переподключения...")
        self.current_state = 'create_request'

    def cleanup(self):


        if self.socket:
            self.socket.close()
        print(" Клиент остановлен")


if __name__ == "__main__":
    client = Client_COMPANY_NAME()
    client.start_work_client()
