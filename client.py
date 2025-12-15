import os
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


def _ensure_dirs(base_dir: str) -> None:
    os.makedirs(os.path.join(base_dir, "requests"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "responses"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "processing"), exist_ok=True)


def _make_request_id(counter: int) -> str:
    return f"{time.time_ns()}_{os.getpid()}_{counter}"


class ClientStateMachine:
    state = StateDescriptor(
        allowed_states={"CREATE_REQUEST", "AWAIT_RESPONSE", "READ_RESPONSE", "ERROR_HANDLING"},
        initial_state="CREATE_REQUEST",
    )

    def __init__(self, channel_dir: str, timeout: float = 10.0, poll_interval: float = 0.05):
        self.channel_dir = channel_dir
        self.timeout = float(timeout)
        self.poll_interval = float(poll_interval)
        self.work = True
        self.current_request = ""
        self.request_id = ""
        self.response_text = ""
        self._counter = 0
        self.state = "CREATE_REQUEST"
        _ensure_dirs(self.channel_dir)

    def create_request(self):
        self.current_request = input("Введите запрос: ").strip()
        if self.current_request.lower() == "exit":
            self.work = False
            return
        self._counter += 1
        self.request_id = _make_request_id(self._counter)
        req_dir = os.path.join(self.channel_dir, "requests")
        tmp_path = os.path.join(req_dir, f"{self.request_id}.tmp")
        req_path = os.path.join(req_dir, f"{self.request_id}.req")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(self.current_request)
        os.replace(tmp_path, req_path)
        self.state = "AWAIT_RESPONSE"

    def await_response(self):
        resp_dir = os.path.join(self.channel_dir, "responses")
        resp_path = os.path.join(resp_dir, f"{self.request_id}.resp")
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            if os.path.exists(resp_path):
                self.state = "READ_RESPONSE"
                return
            time.sleep(self.poll_interval)
        self.state = "ERROR_HANDLING"

    def read_response(self):
        resp_dir = os.path.join(self.channel_dir, "responses")
        resp_path = os.path.join(resp_dir, f"{self.request_id}.resp")
        try:
            with open(resp_path, "r", encoding="utf-8", errors="replace") as f:
                self.response_text = f.read()
            try:
                os.remove(resp_path)
            except OSError:
                pass
            print(f"Ответ: '{self.response_text}'")
            self.state = "CREATE_REQUEST"
        except Exception:
            self.state = "ERROR_HANDLING"

    def handle_error(self):
        try:
            _ensure_dirs(self.channel_dir)
        except Exception:
            pass
        time.sleep(0.3)
        self.state = "CREATE_REQUEST"

    def run(self):
        print(f"Канал: {self.channel_dir}")
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
                    break
            except KeyboardInterrupt:
                break
            except Exception:
                self.state = "ERROR_HANDLING"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--channel", default=None)
    p.add_argument("--port", type=int, default=12345)
    p.add_argument("--timeout", type=float, default=10.0)
    args, rest = p.parse_known_args()
    channel = args.channel
    if channel is None:
        if rest:
            if rest[0].isdigit():
                channel = f"channel_{int(rest[0])}"
            else:
                channel = rest[0]
        else:
            channel = f"channel_{args.port}"
    return channel, args.timeout


if __name__ == "__main__":
    channel, timeout = parse_args()
    ClientStateMachine(channel_dir=channel, timeout=timeout).run()
