"""
*   FILE          : service.py
*   PROJECT       : Logging Service - A3
*   PROGRAMMER    : Warren, Ahmed
*   FIRST VERSION : 01/31/2025
*   DESCRIPTION   :
*      This file is for the logging service. It handles client connections, logs messages to a file, and enforces rate limiting to prevent abuse.
"""

import socket
import threading
import time
import sys
from datetime import datetime

class LoggingServer:

    """
        *  Function  : __init__()
        *  Summary   : Initializes the logging server with port, log file, and rate limit settings.
        *  Params    :
        *     port (int)          
        *     logFile (str)       
        *     rateLimit (int)     
        *  Return    : None.
    """
    def __init__(self, port, logFile, rateLimit):
        self.port = int(port)
        self.logFile = logFile
        self.rateLimit = int(rateLimit)  # Maximum logs per second per client
        self.rateWindow = 1  
        self.logFormat = "{timeStamp} | {clientId} | {category} | {message}"  #  log format
        self.clientRates = {}  # Track client message rate
        self.lock = threading.Lock()
        self.fileLock = threading.Lock()
    
    """
        *  Function  : start()
        *  Summary   : Starts the logging server and listens for incoming client connections.
        *  Params    : None.
        *  Return    : None.
    """
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(('0.0.0.0', self.port))
            server.listen()
            print(f"Logging server started on port {self.port}, writing logs to {self.logFile}")
            while True:
                conn, addr = server.accept()
                print(f"Connected by {addr}")
                clientThread = threading.Thread(target=self.handleClient, args=(conn, addr))
                clientThread.start()

    """
        *  Function  : handleClient()
        *  Summary   : Handles an individual client connection, reading and logging messages.
        *  Params    :
        *     conn (socket) 
        *     addr   
        *  Return    : None.
    """
    def handleClient(self, conn, addr):
        clientId = f"{addr[0]}:{addr[1]}"
        try:
            with conn:
                file = conn.makefile('r')
                # This logs when the client connects
                timeStamp = datetime.utcnow().isoformat()
                connectionLog = self.logFormat.format(
                    timeStamp=timeStamp,
                    clientId=clientId,
                    category="CONNECTED",
                    message="Client has connected."
                )
                self.writeLog(connectionLog)
                while True:
                    line = file.readline().strip()
                    if not line:
                        break

                    parts = line.split('|')
                    if len(parts) < 3:
                        print(f"Invalid log message from {addr}")
                        continue

                    clientId = parts[0].strip()
                    category = parts[1].strip()
                    message = parts[2].strip()

                    if not clientId or not category or not message:
                        print(f"Missing fields from {addr}")
                        continue

                    # Rate limiting
                    allowed = self.checkRateLimit(clientId)
                    if not allowed:
                        print(f"Rate limit exceeded for client {clientId}")
                        continue

                    # Log entry formatting
                    timeStamp = datetime.utcnow().isoformat()
                    logEntry = self.logFormat.format(
                        timeStamp=timeStamp,
                        clientId=clientId,
                        category=category,
                        message=message
                    )
                    self.writeLog(logEntry)

                    
        except Exception as e:
            print(f"Error handling client {addr}: {e}")

        finally:
            # This logs when the client disconnects
            timeStamp = datetime.utcnow().isoformat()
            disconnectionLog = self.logFormat.format(
                timeStamp=timeStamp,
                clientId=clientId,
                category="DISCONNECTED",
                message="Client has disconnected."
            )
            self.writeLog(disconnectionLog)
            print(f"Client {clientId} disconnected.")

    
    """
        *  Function  : writeLog()
        *  Summary   : Writes a log entry to the log file.
        *  Params    :
        *     logEntry 
        *  Return    : None.
    """
    def writeLog(self, logEntry):
        with self.fileLock:
            with open(self.logFile, 'a') as logFilee:
                logFilee.write(logEntry + '\n')

    """
        *  Function  : checkRateLimit()
        *  Summary   : Checks if a client has exceeded the rate limit for logging.
        *  Params    :
        *     clientId 
        *  Return    :
        *     bool : True if the client is allowed to log, False if rate limit is exceeded.
        """
    def checkRateLimit(self, clientId):
        with self.lock:
            currentTime = time.time()
            if clientId not in self.clientRates:
                self.clientRates[clientId] = (currentTime, 1)
                return True
            else:
                startTime, count = self.clientRates[clientId]
                elapsed = currentTime - startTime
                if elapsed > self.rateWindow:
                    self.clientRates[clientId] = (currentTime, 1)
                    return True
                else:
                    if count < self.rateLimit:
                        self.clientRates[clientId] = (startTime, count + 1)
                        return True
                    else:
                        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python service.py <port> <logfile> <rate_limit>")
        sys.exit(1)

    
    server = LoggingServer(sys.argv[1], sys.argv[2], sys.argv[3])
    server.start()