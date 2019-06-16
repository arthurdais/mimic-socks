
import select
from bytes_producer import BytesProducer

buffer_size = 4096

class SocketBytesProducer(BytesProducer):
    def __init__(self, source):
        super(SocketBytesProducer, self).__init__(source, buffer_size)

    def _produce(self, max_size):
        #等待数据
        r, w, e = select.select([self._source], [], [])
        data = self._source.recv(min(buffer_size, max_size))
        for byte in data:
            self._buffer.put(bytes([byte]))
        return len(data)
