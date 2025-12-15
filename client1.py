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


class ClientStateMachine:
    state = StateDescriptor(
        allowed_states={"CREATE_REQUEST", "AWAIT_RESPONSE", "CLEANUP", "ERROR"},
        initial_state="CREATE_REQUEST",
    )

    def __init__(self, channel_name: str, timeout: float = 10.0):
        self.request_pipe_path = f"/tmp/{channel_name}.req.pipe"
        self.timeout = timeout
        self._counter = 0
        self._current_response_pipe = None

    def run(self):
        print(f"Клиент запущен. Канал запросов: {self.request_pipe_path}")
        if not os.path.exists(self.request_pipe_path):
            print("Ошибка: Канал запросов сервера не найден. Запустите сервер.")
            return

        try:
            while True:
                self.state = "CREATE_REQUEST"
                request_text = input("Введите запрос (ping/exit): ").strip()

                if request_text.lower() == 'exit':
                    break

                # 1. Создаем свой УНИКАЛЬНЫЙ FIFO для получения ответа
                self._counter += 1
                response_pipe_path = f"/tmp/resp_{os.getpid()}_{self._counter}.pipe"
                self._current_response_pipe = response_pipe_path
                os.mkfifo(response_pipe_path)

                self.state = "AWAIT_RESPONSE"
                try:
                    # 2. Отправляем запрос серверу.
                    req_fd = os.open(self.request_pipe_path, os.O_WRONLY)
                    message = f"{request_text}:{response_pipe_path}"
                    os.write(req_fd, message.encode('utf-8'))
                    os.close(req_fd)

                    # 3. Открываем свой FIFO и ЖДЕМ ответа (блокирующий вызов)
                    resp_fd = os.open(response_pipe_path, os.O_RDONLY)
                    response_bytes = os.read(resp_fd, 1024)
                    os.close(resp_fd)

                    print(f"Получен ответ: '{response_bytes.decode('utf-8')}'")

                except FileNotFoundError:
                    print("Ошибка: Не удалось подключиться к каналу сервера.")
                    time.sleep(1)  # Пауза перед повторной попыткой
                except Exception as e:
                    self.state = "ERROR"
                    print(f"Произошла ошибка: {e}")
                    traceback.print_exc()
                finally:
                    # 4. Обязательно удаляем свой FIFO после использования
                    self.state = "CLEANUP"
                    if os.path.exists(self._current_response_pipe):
                        os.unlink(self._current_response_pipe)
                    self._current_response_pipe = None

        except KeyboardInterrupt:
            print("\nЗавершение работы клиента.")
        finally:
            # Если вышли из цикла по Ctrl+C, тоже подчищаем
            if self._current_response_pipe and os.path.exists(self._current_response_pipe):
                os.unlink(self._current_response_pipe)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("channel", nargs="?", default="my_channel_12345")
    p.add_argument("--timeout", type=float, default=10.0)
    args = p.parse_args()
    return args.channel, args.timeout


if __name__ == "__main__":
    channel, timeout = parse_args()
    ClientStateMachine(channel_name=channel, timeout=timeout).run()

