import os
import time
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


def _ensure_dirs(base_dir: str) -> None:
    os.makedirs(os.path.join(base_dir, "requests"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "responses"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "processing"), exist_ok=True)


class RequestSession:
    state = StateDescriptor(
        allowed_states={"TAKE", "PROCESS", "WRITE", "DONE", "ERROR"},
        initial_state="TAKE",
    )

    def __init__(self, channel_dir: str, filename: str):
        self.channel_dir = channel_dir
        self.filename = filename
        self.state = "TAKE"

    def run(self):
        reqs = os.path.join(self.channel_dir, "requests")
        procs = os.path.join(self.channel_dir, "processing")
        resps = os.path.join(self.channel_dir, "responses")

        req_path = os.path.join(reqs, self.filename)
        proc_path = os.path.join(procs, self.filename)

        try:
            os.replace(req_path, proc_path)
        except FileNotFoundError:
            return
        except Exception:
            return

        try:
            self.state = "PROCESS"
            with open(proc_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

            response = process_request_text(text)

            self.state = "WRITE"
            req_id = os.path.splitext(self.filename)[0]
            tmp_resp = os.path.join(resps, f"{req_id}.tmp")
            resp_path = os.path.join(resps, f"{req_id}.resp")
            with open(tmp_resp, "w", encoding="utf-8") as f:
                f.write(response)
            os.replace(tmp_resp, resp_path)

            self.state = "DONE"
        except Exception:
            self.state = "ERROR"
        finally:
            try:
                os.remove(proc_path)
            except OSError:
                pass


class Server:
    def __init__(self, channel_dir: str, poll_interval: float = 0.05, max_parallel: int = 64):
        self.channel_dir = channel_dir
        self.poll_interval = float(poll_interval)
        self.max_parallel = int(max_parallel)
        self._active = set()
        self._lock = threading.Lock()
        _ensure_dirs(self.channel_dir)

    def _start_session(self, filename: str):
        def worker():
            try:
                RequestSession(self.channel_dir, filename).run()
            finally:
                with self._lock:
                    self._active.discard(threading.current_thread())

        t = threading.Thread(target=worker, daemon=True)
        with self._lock:
            if len(self._active) >= self.max_parallel:
                return
            self._active.add(t)
        t.start()

    def start(self):
        print(f"Канал: {self.channel_dir}")
        reqs = os.path.join(self.channel_dir, "requests")
        try:
            while True:
                try:
                    files = [f for f in os.listdir(reqs) if f.endswith(".req")]
                except FileNotFoundError:
                    _ensure_dirs(self.channel_dir)
                    files = []

                for fn in files:
                    self._start_session(fn)

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            pass


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--channel", default=None)
    p.add_argument("--port", type=int, default=12345)
    p.add_argument("--poll", type=float, default=0.05)
    p.add_argument("--max-parallel", type=int, default=64)
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
    return channel, args.poll, args.max_parallel


if __name__ == "__main__":
    channel, poll, max_parallel = parse_args()
    Server(channel_dir=channel, poll_interval=poll, max_parallel=max_parallel).start()
