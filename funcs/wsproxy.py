#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function
import socket
import threading
import _thread
import select
import signal
import sys
import time
import getopt

PASS = ''
LISTENING_ADDR = '0.0.0.0'
try:
    LISTENING_PORT = int(sys.argv[1])
except IndexError:
    LISTENING_PORT = 80
BUFLEN = 4096 * 4
TIMEOUT = 60
MSG = ''
COR = '<font color="null">'
FTAG = '</font>'
DEFAULT_HOST = "127.0.0.1:22"
RESPONSE = 'HTTP/1.1 101 Protocols Switched <strong> ⚙︎ Voltssh-X ULTIMATE by @voltsshx ⚙︎</strong>\r\n\r\n'

class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.running = False
        self.host = host
        self.port = port
        self.threads = []
        self.threadsLock = threading.Lock()
        self.logLock = threading.Lock()

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
                    c.setblocking(1)
                except socket.timeout:
                    continue

                conn = ConnectionHandler(c, self, addr)
                conn.start()
                self.addConn(conn)
        finally:
            self.running = False
            self.soc.close()

    def print_log(self, log):
        with self.logLock:
            print(log)

    def add_conn(self, conn):
        with self.threadsLock:
            if self.running:
                self.threads.append(conn)

    def remove_conn(self, conn):
        with self.threadsLock:
            self.threads.remove(conn)

    def close(self):
        with self.threadsLock:
            self.running = False
            for c in self.threads:
                c.close()

class ConnectionHandler(threading.Thread):
    def __init__(self, soc_client, server, addr):
        threading.Thread.__init__(self)
        self.client_closed = False
        self.target_closed = True
        self.client = soc_client
        self.client_buffer = ''
        self.server = server
        self.log = 'Connection: ' + str(addr)

    def close(self):
        try:
            if not self.client_closed:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
        except Exception as e:
            print(f"Error closing client socket: {e}")
        finally:
            self.client_closed = True

        try:
            if not self.target_closed:
                self.target.shutdown(socket.SHUT_RDWR)
                self.target.close()
        except Exception as e:
            print(f"Error closing target socket: {e}")
        finally:
            self.target_closed = True

    def run(self):
        try:
            self.client_buffer = self.client.recv(BUFLEN)

            host_port = self.find_header(self.client_buffer, 'X-Real-Host')

            if host_port == '':
                host_port = DEFAULT_HOST

            split = self.find_header(self.client_buffer, 'X-Split')

            if split != '':
                self.client.recv(BUFLEN)

            if host_port != '':
                passwd = self.find_header(self.client_buffer, 'X-Pass')

                if len(PASS) != 0 and passwd == PASS:
                    self.method_CONNECT(host_port)
                elif len(PASS) != 0 and passwd != PASS:
                    self.client.send('HTTP/1.1 400 WrongPass!\r\n\r\n'.encode())
                elif host_port.startswith('127.0.0.1') or host_port.startswith('localhost'):
                    self.method_CONNECT(host_port)
                else:
                    self.client.send('HTTP/1.1 403 Forbidden!\r\n\r\n'.encode())
            else:
                print('- No X-Real-Host!')
                self.client.send('HTTP/1.1 400 NoXRealHost!\r\n\r\n'.encode())

        except Exception as e:
            self.log += ' - error: ' + str(e)
            self.server.print_log(self.log)
        finally:
            self.close()
            self.server.remove_conn(self)

    def find_header(self, head, header):
        aux = head.find(header + ': ')

        if aux == -1:
            return ''

        aux = head.find(':', aux)
        head = head[aux + 2:]
        aux = head.find('\r\n')

        if aux == -1:
            return ''

        return head[:aux]

    def connect_target(self, host):
        i = host.find(':')
        if i != -1:
            port = int(host[i + 1:])
            host = host[:i]
        else:
            if self.method == 'CONNECT':
                port = 443
            else:
                port = 80

        (soc_family, soc_type, proto, _, address) = socket.getaddrinfo(host, port)[0]

        self.target = socket.socket(soc_family, soc_type, proto)
        self.target_closed = False
        self.target.connect(address)

    def method_CONNECT(self, path):
        self.log += ' - CONNECT ' + path

        self.connect_target(path)
        self.client.sendall(RESPONSE.encode())
        self.client_buffer = ''

        self.server.print_log(self.log)
        self.do_CONNECT()

    def do_CONNECT(self):
        socs = [self.client, self.target]
        count = 0
        error = False
        while True:
            count += 1
            (recv, _, err) = select.select(socs, [], socs, 3)
            if err:
                error = True
            if recv:
                for in_ in recv:
                    try:
                        data = in_.recv(BUFLEN)
                        if data:
                            if in_ is self.target:
                                self.client.send(data)
                            else:
                                while data:
                                    byte = self.target.send(data)
                                    data = data[byte:]

                            count = 0
                        else:
                            break
                    except Exception as e:
                        error = True
                        print(f"Error during data transfer: {e}")
                        break
            if count == TIMEOUT:
                error = True

            if error:
                break

def print_usage():
    print('Use: proxy.py -p <port>')
    print('       proxy.py -b <ip> -p <porta>')
    print('       proxy.py -b 0.0.0.0 -p 22')

def parse_args(argv):
    global LISTENING_ADDR
    global LISTENING_PORT

    try:
        opts, args = getopt.getopt(argv, "hb:p:", ["bind=", "port="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-b", "--bind"):
            LISTENING_ADDR = arg
        elif opt in ("-p", "--port"):
            LISTENING_PORT = int(arg)

def main(host=LISTENING_ADDR, port=LISTENING_PORT):
    print("\033[0;34m━" * 8, "\033[1;32m WebSocket", "\033[0;34m━" * 8, "\n")
    print("\033[1;33mHost/IP:\033[1;32m " + LISTENING_ADDR)
    print("\033[1;33mPort:\033[1;32m " + str(LISTENING_PORT) + "\n")
    print("\033[0;34m⚙︎" * 10, "\033[1;32m  Voltssh-X 'ULTIMATE' by @voltsshx", "\033[0;34m⚙︎\033[1;37m" * 11, "\n")

    server = Server(LISTENING_ADDR, LISTENING_PORT)
    server.start()

    while True:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print('stopping...')
            server.close()
            break

if __name__ == '__main__':
    parse_args(sys.argv[1:])
    main()
