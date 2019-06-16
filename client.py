
import logging
import socket
from socketserver import StreamRequestHandler, ThreadingTCPServer
from util import SOCKS_VERSION, SOCKET_TIMEOUT, secure_sock, generate_failed_reply

address_type = 1 # ipv4
# server_bind_info = ('127.0.0.1', 10232)
server_bind_info = ('188.166.113.223', 10232)

logging.basicConfig(level=logging.INFO)

class Client(StreamRequestHandler):
    def handle(self):
        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(SOCKET_TIMEOUT)
            remote.connect(server_bind_info)
            bind_address = remote.getsockname()
            logging.info('Connected to %s %s' % (server_bind_info))
            secure_sock.exchange_loop(self.connection, remote, False)
        except Exception as err:
            logging.error(err)
            # 响应拒绝连接的错误
            reply = generate_failed_reply(address_type, 5)
            self.connection.sendall(reply)

        self.server.close_request(self.request)

if __name__ == '__main__':
    # 使用socketserver库的多线程服务器ThreadingTCPServer启动代理
    with ThreadingTCPServer(('127.0.0.1', 9011), Client) as server:
        print('client proxy started!')
        server.serve_forever()
