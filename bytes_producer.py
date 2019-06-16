
from abc import ABCMeta, abstractmethod
from queue import Queue

class BytesProducer(metaclass=ABCMeta):
    def __init__(self, source, max_queue_size):
        self._source = source
        self._buffer = Queue(max_queue_size) if (max_queue_size>0) else Queue()

    # size 表示一次性消费的字节数
    def consume(self, size):
        byte_array = b''
        left_size = size
        while left_size > 0:
            available_size = min(self._buffer.qsize(), left_size)
            for i in range(available_size):
                byte_array += self._buffer.get()
            left_size -= available_size
            if left_size > 0:
                produced_num = self._produce(left_size)
                if produced_num == 0:
                    raise RuntimeError('Socket ' + str(self._source) + ' read failed!')
        return byte_array

    # return produced byte num
    @abstractmethod
    def _produce(self, max_size):
        pass
