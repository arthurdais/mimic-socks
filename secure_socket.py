
from random import randint, sample, choice
import string
from Crypto.Cipher import AES
import struct
import select
import logging
from socket_bytes_producer import SocketBytesProducer

ENCODING = 'utf-8'
LEN_COLUMN_LEN = 6
iv_param = 'This is an IV456'
CRYPTO_INPUT_LEN_UNIT = 16
CIPHER_LEN_UNIT = 16 # aes密文长度为16的倍数
MAX_SALT_LEN = CIPHER_LEN_UNIT * 100 - 1 # 必须为此形式，否则pack数据长度(对CIPHER_LEN_UNIT取模)分布将具备可检测特征

logging.basicConfig(level=logging.INFO)

class SecureSocket:
    def __init__(self, crypto, password):
        super(SecureSocket, self).__init__()
        self.crypto = crypto
        self.password = password

    def exchange_loop(self, client, remote, client_encode):
        client_bytes_producer = SocketBytesProducer(client)
        remote_bytes_producer = SocketBytesProducer(remote)

        while True:
            # 等待数据
            r, w, e = select.select([client, remote], [], [])
            if client in r:
                if not self.recv_and_send_data(client, remote, client_encode, client_bytes_producer):
                    break
            if remote in r:
                if not self.recv_and_send_data(remote, client, not client_encode, remote_bytes_producer):
                    break

    def recv_and_send_data(self, source, target, source_encode, source_bytes_producer):
        if source_encode:
            data = self.unpack_data(source, source_bytes_producer)
        else:
            data = self.pack_data(source.recv(4096))
        if len(data) == 0:
            return False
        try:
            target.sendall(data)
        except Exception as err:
            logging.error(err)
            return False
        return True

    def pack_data(self, data):
        data_len = len(data)
        data_cipher = self._encode_data(data)

        salt = SecureSocket._rand_bytes(randint(0, MAX_SALT_LEN))

        header = struct.pack("!HHH", len(data_cipher), len(salt), data_len)
        header_cipher = self._encode_data(header)

        return header_cipher + data_cipher + salt

    def unpack_data(self, source, source_bytes_producer=None):
        if source_bytes_producer == None:
            source_bytes_producer = SocketBytesProducer(source)
        header_cipher = source_bytes_producer.consume(CIPHER_LEN_UNIT)
        header = self._decode_data(header_cipher)
        data_cipher_len, salt_len, data_len = struct.unpack("!HHH", header[:6])
        data_cipher = source_bytes_producer.consume(data_cipher_len)
        data = self._decode_data(data_cipher)[:data_len]
        source_bytes_producer.consume(salt_len) # abandon salt
        return data

    def _encode_data(self, data):
        data = SecureSocket._data_to_crypto_input(data)
        return self._new_crypto_instance().encrypt(data)

    def _decode_data(self, data):
        return self._new_crypto_instance().decrypt(data)

    def _new_crypto_instance(self):
        return AES.new(self.password, AES.MODE_CBC, iv_param)

    # 要加密的明文数据，长度必须是16的倍数，在data后添加salt是指满足
    def _data_to_crypto_input(data):
        salt_len = CRYPTO_INPUT_LEN_UNIT - len(data) % CRYPTO_INPUT_LEN_UNIT
        salt = SecureSocket._rand_bytes(salt_len)
        return data + salt

    def _rand_bytes(size):
        result = b''
        for i in range(size):
            result += bytes([randint(0,255)])
        return result

if __name__ == '__main__':
    sock = SecureSocket('', 'ThisIs SecretKey')
    original_data = b'1234567890123456'
    print('original_data = ' + str(original_data))
    encoded_data = sock._encode_data(original_data)
    print('encoded_data = ' + str(encoded_data))
    decoded_data = sock._decode_data(encoded_data)
    print('decoded_data = ' + str(decoded_data))
