
from secure_socket import SecureSocket
import struct

ENCODING = 'utf-8'

SOCKS_VERSION = 5

SOCKET_TIMEOUT = 10 # seconds

secure_sock = SecureSocket('', 'ThisIs SecretKey')

def generate_failed_reply(address_type, error_number):
    return struct.pack("!BBBBIH", SOCKS_VERSION, error_number, 0, address_type, 0, 0)
