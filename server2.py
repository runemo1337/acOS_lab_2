import os
import time
import argparse
import traceback

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

class Server:
    state = StateDescriptor(
        allowed_states={"WAITING", "PROCESSING", "RESPONDING", "ERROR"},
        initial_state="WAITING",
    )

    def __init__(self, channel_name: str):
        self.request_pipe_path = f"/tmp/{channel_name}.req.pipe"
        self._req_fd = None

    def start(self):
        print(f"Сервер запущен. Канал запросов: {self.request_pipe_path}")

        # 1. Создаем главный FIFO для запросов, если он не существует
        if not os.path.exists(self.request_pipe_path):
            os.mkfifo(self.request_pipe_path)

        try:
            # 2. Открываем FIFO на чтение. Этот вызов не блокируется.
            # Число писло
            self._req_fd = os.open(self.request_pipe_path, os.O_RDONLY)
            print("Ожидание запросов...")

            while True:
                self.state = "WAITING"
                # Чтение
                request_bytes = os.read(self._req_fd, 1024)
                if not request_bytes: #переоткрываем канал
                    os.close(self._req_fd)
                    self._req_fd = os.open(self.request_pipe_path, os.O_RDONLY)
                    continue

                self.state = "PROCESSING"
                try:
                    request_str = request_bytes.decode('utf-8')
                    req_text, response_pipe_path = request_str.strip().split(":", 1)
                except (UnicodeDecodeError, ValueError) as e:
                    print(f"Ошибка: Некорректный формат запроса. {e}")
                    self.state = "ERROR"
                    continue

                print(f"Получен запрос: '{req_text}' | Канал ответа: {response_pipe_path}")
                response_text = process_request_text(req_text)

                self.state = "RESPONDING"
                try:
                    resp_fd = os.open(response_pipe_path, os.O_WRONLY)
                    os.write(resp_fd, response_text.encode('utf-8'))
                    os.close(resp_fd)
                except OSError as e:
                    print(f"Ошибка: Не удалось отправить ответ клиенту. {e}")
                    self.state = "ERROR"

        except KeyboardInterrupt:
            print("\nЗавершение работы сервера.")
        except Exception as e:
            print(f"Критическая ошибка сервера: {e}")
            traceback.print_exc()
        finally:
            if self._req_fd is not None:
                os.close(self._req_fd)
            if os.path.exists(self.request_pipe_path):
                os.unlink(self.request_pipe_path)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("channel", nargs="?", default="my_channel_12345")
    args = p.parse_args()
    return args.channel

if __name__ == "__main__":
    channel = parse_args()
    Server(channel_name=channel).start()
