from labdevices.scpi import SCPIDeviceEthernet
from select import select
from time import time

class Instrument(SCPIDeviceEthernet):
    def __init__(self, host, port = 5555, *args, **kwargs):
        super().__init__(address = host, port=port, logger = None, *args, **kwargs)
        self.chunk_size = 250_000
        self.connect()
        self._socket.settimeout(10)
    
    def get_identification(self):
        return self.ask("*IDN?")
    
    def write(self, command):
        self.scpiCommand(command)
        return

    def sendall(self, data):
        self._socket.sendall(data)
    
    def recv_n(self, n):
        buff = self._socket.recv(n)
        while len(buff) < n:
            buff += self._socket.recv(n-len(buff))
        return buff

    def recv(self, n):
        return self._socket.recv(n)
    
    def recv_bytes(self, termination="\r\n"):
        header = self.recv_n(2).decode("utf-8")
        assert header[0] == '#', f"{header}"
        digits_read = int(header[1])
        data_len = int(self.recv_n(digits_read).decode("utf-8")) 
        data_len += len(termination)
        raw = self._socket.recv(data_len)
        data_read = len(raw)
        while (data_read < data_len):
            raw += self._socket.recv(data_len)
            data_read = len(raw)
        if len(termination) == 0:
            return raw
        else:
            assert raw[-len(termination):].decode("utf-8") == termination, f"termination = {raw[-len(termination):]}"
        return raw[:-len(termination)]

    def recv_chunk(self, expected_points=None):
        #recv_into(buffer[, nbytes[, flags]])
        raw = self._socket.recv(self.chunk_size)
        data_len = int(raw[2:11].decode("utf-8")) + 12
        #print(raw[:11])
        if expected_points is not None:
            assert data_len == expected_points + 12, f"data_len {data_len}, expected_points {expected_points + 12}"
        data_read = len(raw)
        while (data_read < data_len):
            raw += self._socket.recv(data_len)
            data_read = len(raw)
        assert chr(raw[-1])=='\n'
        return raw
    
    def ask(self, query):
        return self.scpiQuery(query)

    def ask_raw(self, query):
        if not self.isConnected():
            raise CommunicationError_NotConnected("Device not connected")
        self._socket.sendall(query)
        readData = b""

        while True:
            dataBlock = self._socket.recv(4096*10)
            readData = readData + dataBlock
        return readData
    
    def read_raw(self):
        while True:
            dataBlock = self._socket.recv(4096*10)
            dataBlockStr = dataBlock.decode("utf-8")
            readData = readData + dataBlockStr
            if dataBlockStr[-1] == '\n':
                break

    def flush(self):
        while 1:
            inputready, o, e = select([self._socket],[],[], 1.0)
            if len(inputready)==0: break
            for s in inputready: s.recv(1024)
    
    def close(self):
        self.disconnect()