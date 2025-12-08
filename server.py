import socket
import time
class Server_company_name:
    def __init__(self):
        self.current_state = 'Waiting_request'
        self.socket = None
        self.client_socket = None
        self.client_address = None
        self.current_request = None
        self.response_data = None
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
        elif self.current_state == 'PROCESS_REQUEST':
            self.process_request()
        elif self.current_state == 'SEND_RESPONSE':
            self.send_response()
        elif self.current_state == 'catch_error':
            self.handle_error()
