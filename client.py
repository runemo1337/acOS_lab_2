import socket
import time
import random


class ClientStateMachine:
    def __init__(self):
        self.state = 'CREATE_REQUEST'
        self.socket = None
        self.current_request = None
        self.server_response = None
