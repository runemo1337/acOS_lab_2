import socket
import time
import random


<<<<<<< HEAD
class StateDescriptor:

    def __init__(self, allowed_states, initial_state):
        self._allowed = set(allowed_states)
        if initial_state not in self._allowed:
            raise ValueError("initial_state must be in allowed_states")
        self._initial = initial_state

    def __set_name__(self, owner, name):
        self._private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._private_name, self._initial)

    def __set__(self, obj, value):
        if value not in self._allowed:
            raise ValueError(f"Invalid state {value!r}. Allowed: {sorted(self._allowed)}")
        setattr(obj, self._private_name, value)


class ClientStateMachine:

    state = StateDescriptor(
        allowed_states={'CREATE_REQUEST', 'AWAIT_RESPONSE', 'READ_RESPONSE', 'ERROR_HANDLING'},
        initial_state='CREATE_REQUEST'
    )

=======
class Client_COMPANY_NAME:
>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587
    def __init__(self):
        self.current_state = 'create_request'
        self.socket = None
        self.current_request = None
<<<<<<< HEAD
        self.server_response = None
        self.work = True

    def connect_to_server(self):

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
=======
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



>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587
        self.current_request = input("Введите запрос для сервера: ").strip()


        if self.current_request.lower() == 'exit':
            print(" Завершение работы...")
            self.work = False
            return

<<<<<<< HEAD
    def await_response(self):
=======

        print(f"Создан запрос: '{self.current_request}'")
        self.current_state = 'await_answer'

    def send_and_wait(self):
>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587

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
<<<<<<< HEAD
            print(f"Ошибка отправки: {e}")
            self.state = 'ERROR_HANDLING'

    def read_response(self):
=======
            print(f" Ошибка отправки: {e}")
            self.current_state = 'catch_error'

    def read_answer_func(self):
>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587

        try:
            answer = self.socket.recv(1024).decode(self.encoder)
            if answer:
                self.server_answer = answer
                print(f"Получен ответ: '{self.server_answer}'")
                self.current_state = 'create_request'
            else:
<<<<<<< HEAD
                print("Сервер закрыл соединение")
                self.state = 'ERROR_HANDLING'
=======
                print(" Сервер закрыл соединение")
                self.socket.close()
                self.socket = None
                self.current_state = 'catch_error'
>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587

        except socket.timeout:
            print(" Таймаут ожидания ответа")
            self.current_state = 'catch_error'
        except Exception as e:
            print(f" Ошибка чтения: {e}")
            self.current_state = 'catch_error'

<<<<<<< HEAD
    def handle_error(self):

        print("[ERROR_HANDLING] Обработка ошибки...")
=======
    def editing_error(self):

        print(" Обработка ошибки клиента...")

>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587
        if self.socket:
            self.socket.close()
            self.socket = None

        time.sleep(3)
        print(" Попытка переподключения...")
        self.current_state = 'create_request'

    def cleanup(self):

<<<<<<< HEAD
    def run(self):

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

=======

        if self.socket:
            self.socket.close()
        print(" Клиент остановлен")
>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587

if __name__ == "__main__":
<<<<<<< HEAD
    client = ClientStateMachine()
    client.run()
=======
    client = Client_COMPANY_NAME()
    client.start_work_client()
>>>>>>> 4ee04f8873d204098d6674d46c8ba15ff7a55587
