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

    def handle_client(self, conn, addr):
        try:
            with conn:
                file = conn.makefile('r')
                while True:
                    line = file.readline().strip()
                    if not line:
                        break

                    parts = line.split('|')
                    if len(parts) < 3:
                        print(f"Invalid log message from {addr}")
                        continue

                    client_id = parts[0].strip()
                    category = parts[1].strip()
                    message = parts[2].strip()

                    if not client_id or not category or not message:
                        print(f"Missing fields from {addr}")
                        continue

                    # Rate limiting
                    allowed = self.check_rate_limit(client_id)
                    if not allowed:
                        print(f"Rate limit exceeded for client {client_id}")
                        continue

                    # Log entry formatting
                    timestamp = datetime.utcnow().isoformat()
                    log_entry = self.log_format.format(
                        timestamp=timestamp,
                        client_id=client_id,
                        category=category,
                        message=message
                    )

                    # Save log entry to file
                    with self.file_lock:
                        with open(self.logfile, 'a') as file:
                            file.write(log_entry + '\n')
        except Exception as e:
            print(f"Error handling client {addr}: {e}")

    def check_rate_limit(self, client_id):
        with self.lock:
            current_time = time.time()
            if client_id not in self.client_rates:
                self.client_rates[client_id] = (current_time, 1)
                return True
            else:
                start_time, count = self.client_rates[client_id]
                elapsed = current_time - start_time
                if elapsed > self.rate_window:
                    self.client_rates[client_id] = (current_time, 1)
                    return True
                else:
                    if count < self.rate_limit:
                        self.client_rates[client_id] = (start_time, count + 1)
                        return True
                    else:
                        return False
