#!/usr/bin/env python3
# encoding: utf-8

import socket
import threading
import select
import signal
import sys
import time
from os import system

system("clear")

# Configuration
IP = '0.0.0.0'
try:
    PORT = int(sys.argv[1])
except:
    PORT = 80

PASS = ''
BUFLEN = 8196 * 8
TIMEOUT = 60
DEFAULT_HOST = '0.0.0.0:22'
RESPONSE = 'HTTP/1.1 101 Protocols Switched <strong> ⚙︎ Voltssh-X ULTIMATE by @deviyke ⚙︎</strong>\r\n\r\n'

class Server(threading.Thread):
    def __init__(self, host, port):
        if sys.version_info[0] == 2:
            threading.Thread.__init__(self)
        else:
            super().__init__()
        self.running = False
        self.host = host
        self.port = port
        self.threads = []
        self.threadsLock = threading.Lock()

    def run(self):
        self.soc = socket.socket(socket.AF_INET)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.settimeout(2)
        self.soc.bind((self.host, self.port))
        self.soc.listen(0)
        self.running = True

        try:
            while self.running:
                try:
                    c, addr = self.soc.accept()
                    c.setblocking(True)
                    conn = ConnectionHandler(c, self, addr)
                    conn.start()
                    self.addConn(conn)
                except socket.timeout:
                    continue
        finally:
            self.running = False
            self.soc.close()

    def addConn(self, conn):
        with self.threadsLock:
            if self.running:
                self.threads.append(conn)

    def removeConn(self, conn):
        with self.threadsLock:
            if conn in self.threads:
                self.threads.remove(conn)

    def close(self):
        with self.threadsLock:
            self.running = False
            for c in list(self.threads):
                c.close()


class ConnectionHandler(threading.Thread):
    def __init__(self, socClient, server, addr):
        if sys.version_info[0] == 2:
            threading.Thread.__init__(self)
        else:
            super().__init__()
        self.clientClosed = False
        self.targetClosed = True
        self.client = socClient
        self.client_buffer = b''
        self.server = server

    def close(self):
        if not self.clientClosed:
            try:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
            except:
                pass
            self.clientClosed = True

        if not self.targetClosed:
            try:
                self.target.shutdown(socket.SHUT_RDWR)
                self.target.close()
            except:
                pass
            self.targetClosed = True

    def run(self):
        try:
            self.client_buffer = self.client.recv(BUFLEN)
            hostPort = self.findHeader(self.client_buffer, b'X-Real-Host') or DEFAULT_HOST
            split = self.findHeader(self.client_buffer, b'X-Split')
            if split:
                self.client.recv(BUFLEN)

            passwd = self.findHeader(self.client_buffer, b'X-Pass')
            if PASS and passwd == PASS:
                self.method_CONNECT(hostPort)
            elif PASS and passwd != PASS:
                self.client.send(b'HTTP/1.1 400 WrongPass!\r\n\r\n')
            elif hostPort.startswith(IP):
                self.method_CONNECT(hostPort)
            else:
                self.client.send(b'HTTP/1.1 403 Forbidden!\r\n\r\n')
        except Exception as e:
            print('[-] Error: %s' % e)
        finally:
            self.close()
            self.server.removeConn(self)

    def findHeader(self, head, header):
        try:
            lines = head.split(b'\r\n')
            for line in lines:
                if line.lower().startswith(header.lower()):
                    return line.split(b': ')[1].decode()
        except:
            return ''
        return ''

    def connect_target(self, host):
        if ':' in host:
            hostname, port = host.split(':')
            port = int(port)
        else:
            hostname = host
            port = 443 if self.method == 'CONNECT' else 22

        addr_info = socket.getaddrinfo(hostname, port)[0]
        self.target = socket.socket(addr_info[0], addr_info[1], addr_info[2])
        self.targetClosed = False
        self.target.connect(addr_info[4])

    def method_CONNECT(self, path):
        self.method = 'CONNECT'
        self.connect_target(path)
        self.client.sendall(RESPONSE)
        self.client_buffer = b''
        self.doCONNECT()

    def doCONNECT(self):
        socs = [self.client, self.target]
        count = 0
        while True:
            count += 1
            r, _, e = select.select(socs, [], socs, 3)
            if e:
                break
            if r:
                for sock in r:
                    try:
                        data = sock.recv(BUFLEN)
                        if not data:
                            return
                        if sock is self.target:
                            self.client.sendall(data)
                        else:
                            self.target.sendall(data)
                        count = 0
                    except:
                        return
            if count >= TIMEOUT:
                break


def main(host=IP, port=PORT):
    print("\033[0;34m━"*8, "\033[1;32m Socket ", "\033[0;34m━"*8)
    print("\033[1;33mHost/IP:\033[1;32m", IP)
    print("\033[1;33mPort:\033[1;32m", port)
    print("\033[0;34m⚙︎"*10, "\033[1;32mVoltssh-X 'ULTIMATE' *Focused* by @deviyke", "\033[0;34m⚙︎"*11)
    server = Server(host, port)
    server.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print('\n[+] Stopping server...')
        server.close()


if __name__ == '__main__':
    main()