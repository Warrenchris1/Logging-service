import socket
import threading
import time
import argparse
from datetime import datetime

class LoggingServer:
    def __init__(self, port, logfile, rate_limit):
        self.port = port
        self.logfile = logfile
        self.rate_limit = rate_limit  # Maximum logs per second per client
        self.rate_window = 1  
        self.log_format = "{timestamp} | {client_id} | {category} | {message}"  #  log format
        self.client_rates = {}  # Track client message rate
        self.lock = threading.Lock()
        self.file_lock = threading.Lock()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(('0.0.0.0', self.port))
            server.listen()
            print(f"Logging server started on port {self.port}, writing logs to {self.logfile}")
            while True:
                conn, addr = server.accept()
                print(f"Connected by {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
