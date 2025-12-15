import socket
import time
import argparse


class StateDescriptor:
    def __init__(self, allowed_states, initial_state):
        self._allowed = set(allowed_states)
        if initial_state not in self._allowed:
            raise ValueError("initial_state must be in allowed_states")
        self._initial = initial_state
        self._private_name = None

    def __set_name__(self, owner, name):
        self._private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._private_name, self._initial)

    def __set__(self, obj, value):
        if value not in self._allowed:
            raise ValueError(f"Invalid state {value!r}")
        setattr(obj, self._private_name, value)


class ClientStateMachine:
    state = StateDescriptor(
        allowed_states={"CREATE_REQUEST", "AWAIT_RESPONSE", "READ_RESPONSE", "ERROR_HANDLING"},
        initial_state="CREATE_REQUEST",
    )

    def __init__(self, host="127.0.0.1", port=12345, timeout=10.0):
        self.host = host
        self.port = port
        self.timeout = float(timeout)
        self.socket = None
        self.current_request = ""
        self.server_response = ""
        self.work = True
        self.state = "CREATE_REQUEST"

    def connect_to_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect((self.host, self.port))
            self.socket = s
            print("Соединение с сервером установлено")
            return True
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            self.state = "ERROR_HANDLING"
            return False

    def create_request(self):
        self.current_request = input("Введите запрос для сервера: ").strip()
        if self.current_request.lower() == "exit":
            self.work = False
            return
        self.state = "AWAIT_RESPONSE"

    def await_response(self):
        try:
            if not self.socket:
                raise RuntimeError("no socket")
            self.socket.sendall(self.current_request.encode("utf-8"))
            self.state = "READ_RESPONSE"
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            self.state = "ERROR_HANDLING"

    def read_response(self):
        try:
            if not self.socket:
                raise RuntimeError("no socket")
            data = self.socket.recv(1024)
            if not data:
                print("Сервер закрыл соединение")
                self.state = "ERROR_HANDLING"
                return
            self.server_response = data.decode("utf-8", errors="replace")
            print(f"Получен ответ: '{self.server_response}'")
            self.state = "CREATE_REQUEST"
            time.sleep(0.2)
        except socket.timeout:
            print("Таймаут ожидания ответа")
            self.state = "ERROR_HANDLING"
        except Exception as e:
            print(f"Ошибка чтения: {e}")
            self.state = "ERROR_HANDLING"

    def handle_error(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        time.sleep(0.5)
        if self.work:
            self.connect_to_server()
            if self.socket:
                self.state = "CREATE_REQUEST"

    def run(self):
        print("Клиент запущен")
        if not self.connect_to_server():
            return

        while True:
            try:
                if self.state == "CREATE_REQUEST":
                    self.create_request()
                elif self.state == "AWAIT_RESPONSE":
                    self.await_response()
                elif self.state == "READ_RESPONSE":
                    self.read_response()
                elif self.state == "ERROR_HANDLING":
                    self.handle_error()

                if not self.work:
                    if self.socket:
                        try:
                            self.socket.close()
                        except Exception:
                            pass
                    break
            except KeyboardInterrupt:
                if self.socket:
                    try:
                        self.socket.close()
                    except Exception:
                        pass
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                self.state = "ERROR_HANDLING"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("host", nargs="?", default="127.0.0.1")
    p.add_argument("port", nargs="?", type=int, default=12345)
    p.add_argument("--host", dest="host_opt", default=None)
    p.add_argument("--port", dest="port_opt", type=int, default=None)
    p.add_argument("--timeout", dest="timeout", type=float, default=10.0)
    args = p.parse_args()
    host = args.host_opt or args.host
    port = args.port_opt if args.port_opt is not None else args.port
    return host, port, args.timeout


if __name__ == "__main__":
    host, port, timeout = parse_args()
    ClientStateMachine(host=host, port=port, timeout=timeout).run()
