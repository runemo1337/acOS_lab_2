import socket
import time


class Server_company_name:
    def __init__(self):
        self.current_state = 'Waiting_request'
        self.socket = None
        self.client_socket = None
        self.client_address = None
        self.current_request = None
        self.answer_data = None
        self.process = True

    def start_server(self,
                     adress_family=socket.AF_INET,socket_type=socket.SOCK_STREAM,
                     socket_option=socket.SOL_SOCKET, again_usage=True, is_turn_on=1,
                     host='localhost',port=12345,
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
                self.run_state_machine()
            except KeyboardInterrupt:
                print("\n Стоп")
                self.process = False
                break
            except Exception as e:
                print(f" Server Error: {e}")
                self.current_state = 'catch_error'

        self.cleanup()

    def run_state_machine(self):

        if self.current_state == 'Waiting_request':
            self.func_waiting_request()
        elif self.current_state == 'process_editing':
            self.editing_request()
        elif self.current_state == 'send_answer':
            self.send_answer()
        elif self.current_state == 'catch_error':
            self.handle_error()

    def func_waiting_request(self,
                             time_to_write_request=5.0,
                             max_length_request=1488,decoder='utf-8',
                             exception_data=['','sql','c++']):

        if not self.client_socket:
            try:
                self.client_socket, self.client_address = self.socket.accept()
                self.client_socket.settimeout( time_to_write_request)
                print(f" Подключен: {self.client_address}")
            except socket.timeout:
                return

        try:
            request_from_client = self.client_socket.recv(max_length_request).decode(decoder)
            if request_from_client not in exception_data:
                self.current_request = request_from_client.strip().lower()
                print(f"Получен запрос: '{self.current_request}'")
                self.current_state = 'process_editing'
            else:
                print(" Связь была разорвана")
                self.client_socket.close()
                self.client_socket = None
        except socket.timeout:
            return
        except Exception as e:
            print(f" Ошибка олучения данных: {e}")
            self.current_state = 'catch_error'

    def editing_request(self):

        try:



            if self.current_request == "ping":
                self.answer_data = "pong"

            elif self.current_request == "what is up bro?":
                self.answer_data = "Hello Client!"
            elif self.current_request == "goodbye?":
                self.answer_data = "bye:("
            else:

                self.answer_data = f"{self.current_request}"

            


        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
            self.answer_data = "Ошибка 501"
        print(f"{self.answer_data}")
        self.current_state = 'send_answer'
