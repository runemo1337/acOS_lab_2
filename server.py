import socket
import time
import threading


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


class Server_COMPANY_NAME:

    current_state = StateDescriptor(
        allowed_states={'waiting_request', 'process_editing', 'send_answer', 'catch_error'},
        initial_state='waiting_request'
    )

    def __init__(self):
        self.current_state = 'waiting_request'
        self.socket = None
        self.client_socket = None
        self.client_address = None
        self.current_request = None
        self.answer_data = None
        self.process = True
        self.decoder = 'utf-8'
        self._client_threads = []


    def process_request_text(self, request_text: str) -> str:
        req = (request_text or "").strip().lower()
        if req == "ping":
            return "pong"
        elif req == "what is up bro?":
            return "Hello Client!"
        elif req == "goodbye?":
            return "bye:("
        else:
            return req

    def _client_worker(self, client_socket, client_address,
                       time_to_write_request=10.0, max_length_request=1488):
        try:
            client_socket.settimeout(time_to_write_request)
            print(f" Подключен: {client_address}")

            while self.process:
                try:
                    data = client_socket.recv(max_length_request)
                    if not data:
                        break

                    request = data.decode(self.decoder, errors='replace').strip()
                    if request == "":
                        continue

                    answer = self.process_request_text(request)
                    print(f"Получен запрос от {client_address}: '{request}' -> '{answer}'")
                    client_socket.sendall(answer.encode(self.decoder))
                except socket.timeout:
                    continue
        except Exception as e:
            print(f" Client Error {client_address}: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
            print(f" Отключен: {client_address}")

    def start_work_process(self,
                     adress_family=socket.AF_INET, socket_type=socket.SOCK_STREAM,
                     socket_option=socket.SOL_SOCKET, again_usage=True, is_turn_on=1,
                     host='localhost', port=12345,
                     queue_size=1, server_timeout=5.0):

        self.socket = socket.socket(adress_family, socket_type)
        if again_usage:
            self.socket.setsockopt(socket_option, socket.SO_REUSEADDR, is_turn_on)
        self.socket.bind((host, port))
        self.socket.listen(queue_size)
        self.socket.settimeout(server_timeout)
        print(f" Сервер запущен на {host}:{port} ")
        print("Ожиданиe.........")

        while self.process:
            try:
                try:
                    client_socket, client_address = self.socket.accept()
                except socket.timeout:
                    continue


                th = threading.Thread(
                    target=self._client_worker,
                    args=(client_socket, client_address),
                    daemon=True
                )
                th.start()
                self._client_threads.append(th)

            except KeyboardInterrupt:
                print("\n Стоп")
                self.process = False
                break
            except Exception as e:
                print(f" Server Error: {e}")
                self.current_state = 'catch_error'

        self.cleanup()



    def run_state_machine(self):

        if self.current_state == 'waiting_request':
            self.func_waiting_request()
        elif self.current_state == 'process_editing':
            self.editing_request()
        elif self.current_state == 'send_answer':
            self.send_answer()
        elif self.current_state == 'catch_error':
            self.editing_error()

    def func_waiting_request(self,
                             time_to_write_request=10.0,
                             max_length_request=1488
                             ):

        if not self.client_socket:
            try:
                self.client_socket, self.client_address = self.socket.accept()
                self.client_socket.settimeout(time_to_write_request)
                print(f" Подключен: {self.client_address}")
            except socket.timeout:
                return
            except Exception as e:
                print(f" Ошибка  при поключении: {e}")
                self.current_state = 'catch_error'

        try:
            request_from_client = self.client_socket.recv(max_length_request).decode(self.decoder)

            if request_from_client.strip().lower() != '':
                self.current_request = request_from_client.strip().lower()
                print(f"Получен запрос: '{self.current_request}'")
                self.current_state = 'process_editing'
            else:
                print(" Связь была разорвана")
                self.client_socket.close()
                self.client_socket = None
        except socket.timeout:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
        except Exception as e:
            print(f" Ошибка олучения данных: {e}")
            self.current_state = 'catch_error'

    def editing_request(self):

        try:

            self.answer_data = self.process_request_text(self.current_request)

        except Exception as e:
            print(f"Ошибка обработки: {e}")
            self.answer_data = "Ошибка 501"
        print(f"{self.answer_data}")
        self.current_state = 'send_answer'

    def send_answer(self):

        try:
            if self.client_socket:
                self.client_socket.sendall(self.answer_data.encode(self.decoder))

            self.current_state = 'waiting_request'
        except Exception as e:
            print(f" Ошибка отправки: {e}")
            self.current_state = 'catch_error'

    def editing_error(self):

        print("Возникла ошибка идет обработка...")
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        self.current_state = 'waiting_request'
        print("Обработка прошла успешно!!!!!!!!:))))))")

    def cleanup(self):

        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass
        self.socket = None

        for th in self._client_threads:
            try:
                th.join(timeout=0.2)
            except Exception:
                pass


if __name__ == "__main__":
    server = Server_COMPANY_NAME()
    server.start_work_process()
