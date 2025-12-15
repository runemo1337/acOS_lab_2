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
        print(f"Client On. Pipe: {self.request_pipe_path}")
        if not os.path.exists(self.request_pipe_path):
            print("Err, pipe not exists.")
            return

        try:
            while True:
                self.state = "CREATE_REQUEST"
                request_text = input("Enter request (ping/exit): ").strip()

                if request_text.lower() == 'exit':
                    break

                self._counter += 1
                response_pipe_path = f"/tmp/resp_{os.getpid()}_{self._counter}.pipe"
                self._current_response_pipe = response_pipe_path
                os.mkfifo(response_pipe_path)

                self.state = "AWAIT_RESPONSE"
                try:
                    req_fd = os.open(self.request_pipe_path, os.O_WRONLY)
                    message = f"{request_text}:{response_pipe_path}"
                    os.write(req_fd, message.encode('utf-8'))
                    os.close(req_fd)

                    resp_fd = os.open(response_pipe_path, os.O_RDONLY)
                    response_bytes = os.read(resp_fd, 1024)
                    os.close(resp_fd)

                    print(f"Response: '{response_bytes.decode('utf-8')}'")

                except FileNotFoundError:
                    print("Err: cannot connect to the pipe.")
                    time.sleep(1)
                except Exception as e:
                    self.state = "ERROR"
                    print(f"Error: {e}")
                    traceback.print_exc()
                finally:
                    self.state = "CLEANUP"
                    if os.path.exists(self._current_response_pipe):
                        os.unlink(self._current_response_pipe)
                    self._current_response_pipe = None

        except KeyboardInterrupt:
            print("\nClient work ended.")
        finally:
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

