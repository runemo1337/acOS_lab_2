import socket
import threading
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


def process_request_text(text: str) -> str:
    t = text.strip()
    if t.lower() == "ping":
        return "pong"
    return "error"


class ConnectionSession:
    state = StateDescriptor(
        allowed_states={"WAIT", "PROCESS", "SEND", "CLOSE", "ERROR"},
        initial_state="WAIT",
    )

    def __init__(self, conn: socket.socket, addr):
        self.conn = conn
        self.addr = addr
        self.state = "WAIT"
        self._last_response = ""

    def run(self):
        try:
            while True:
                self.state = "WAIT"
                data = self.conn.recv(1024)
                if not data:
                    self.state = "CLOSE"
                    break

                self.state = "PROCESS"
                text = data.decode("utf-8", errors="replace")
                self._last_response = process_request_text(text)

                self.state = "SEND"
                self.conn.sendall(self._last_response.encode("utf-8"))
        except Exception:
            self.state = "ERROR"
        finally:
            try:
                self.conn.close()
            except Exception:
                pass


class Server:
    def __init__(self, host="0.0.0.0", port=12345, backlog=128):
        self.host = host
        self.port = int(port)
        self.backlog = int(backlog)
        self._sock = None

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(self.backlog)
        self._sock = s
        print(f"Сервер запущен на {self.host}:{self.port}")

        try:
            while True:
                conn, addr = s.accept()
                t = threading.Thread(target=ConnectionSession(conn, addr).run, daemon=True)
                t.start()
        except KeyboardInterrupt:
            pass
        finally:
            try:
                s.close()
            except Exception:
                pass


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("port", nargs="?", type=int, default=12345)
    p.add_argument("--port", dest="port_opt", type=int, default=None)
    p.add_argument("--host", dest="host", default="0.0.0.0")
    args = p.parse_args()
    port = args.port_opt if args.port_opt is not None else args.port
    return args.host, port


if __name__ == "__main__":
    host, port = parse_args()
    Server(host=host, port=port).start()
