
from util import secure_sock
from bytes_producer import BytesProducer

class SecureSocketBytesProducer(BytesProducer):
    def __init__(self, source):
        super(SecureSocketBytesProducer, self).__init__(source, 0)

    # produce one complete unpacked data block, max_size argument ignored
    def _produce(self, max_size):
        data = secure_sock.unpack_data(self._source)
        for byte in data:
            self._buffer.put(bytes([byte]))
        return len(data)
