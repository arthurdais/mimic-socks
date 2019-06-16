# from : https://hatboy.github.io/2018/04/28/Python%E7%BC%96%E5%86%99socks5%E6%9C%8D%E5%8A%A1%E5%99%A8/

import logging
import select
import socket
import struct
from socketserver import StreamRequestHandler, ThreadingTCPServer
from util import ENCODING, SOCKS_VERSION, SOCKET_TIMEOUT, secure_sock, generate_failed_reply
from secure_socket_bytes_producer import SecureSocketBytesProducer

logging.basicConfig(level=logging.INFO)

# server_bind_info = ('127.0.0.1', 10232) # 仅局域网可访问
server_bind_info = ('0.0.0.0', 10232) # 部署到公网ip，内外网均可访问

class Server(StreamRequestHandler):
    def handle(self):
        logging.info('Accepting connection from %s:%s' % self.client_address)
        ss_bytes_producer = SecureSocketBytesProducer(self.connection)
        # 协商
        # 从客户端读取并解包两个字节的数据
        header = ss_bytes_producer.consume(2)
        version, nmethods = struct.unpack("!BB", header)
        # 设置socks5协议，METHODS字段的数目大于0
        assert version == SOCKS_VERSION
        assert nmethods > 0
        # 接受支持的方法
        methods = self.get_available_methods(ss_bytes_producer, nmethods)
        # 检查是否支持用户名/密码认证方式，不支持则断开连接
        if 0 not in set(methods):
            self.server.close_request(self.request)
            return
        # 发送协商响应数据包
        self.connection.send(secure_sock.pack_data(struct.pack("!BB", SOCKS_VERSION, 0)))
        # 请求
        version, cmd, _, address_type = struct.unpack("!BBBB", ss_bytes_producer.consume(4))
        assert version == SOCKS_VERSION
        if address_type == 1:  # IPv4
            address = socket.inet_ntoa(ss_bytes_producer.consume(4))
        elif address_type == 3:  # Domain name
            domain_length = ord(ss_bytes_producer.consume(1))
            address = ss_bytes_producer.consume(domain_length)
            #address = socket.gethostbyname(address.decode("UTF-8"))  # 将域名转化为IP，这一行可以去掉
        elif address_type == 4: # IPv6
            addr_ip = ss_bytes_producer.consume(16)
            address = socket.inet_ntop(socket.AF_INET6, addr_ip)
        else:
            self.server.close_request(self.request)
            return
        port = struct.unpack('!H', ss_bytes_producer.consume(2))[0]
        # 响应，只支持CONNECT请求
        try:
            if cmd == 1:  # CONNECT
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(SOCKET_TIMEOUT)
                remote.connect((address, port))
                bind_address = remote.getsockname()
                logging.info('Connected to %s %s' % (address, port))
            else:
                logging.info('cmd = ' + str(cmd) + ', will close request!')
                self.server.close_request(self.request)
            addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
            port = bind_address[1]
            #reply = struct.pack("!BBBBIH", SOCKS_VERSION, 0, 0, address_type, addr, port)
            # 注意：按照标准协议，返回的应该是对应的address_type，但是实际测试发现，当address_type=3，也就是说是域名类型时，会出现卡死情况，但是将address_type该为1，则不管是IP类型和域名类型都能正常运行
            reply = struct.pack("!BBBBIH", SOCKS_VERSION, 0, 0, 1, addr, port)
        except Exception as err:
            logging.error(err)
            # 响应拒绝连接的错误
            reply = generate_failed_reply(address_type, 5)
        self.connection.sendall(secure_sock.pack_data(reply))
        # 建立连接成功，开始交换数据
        if reply[1] == 0 and cmd == 1:
            secure_sock.exchange_loop(self.connection, remote, True)
        self.server.close_request(self.request)

    def get_available_methods(self, ss_bytes_producer, n):
        methods = []
        for i in range(n):
            methods.append(ord(ss_bytes_producer.consume(1)))
        return methods

if __name__ == '__main__':
    # 使用socketserver库的多线程服务器ThreadingTCPServer启动代理
    with ThreadingTCPServer(server_bind_info, Server) as server:
        print('server proxy started!')
        server.serve_forever()
        