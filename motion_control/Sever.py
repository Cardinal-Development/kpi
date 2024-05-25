import logging
import threading
import time
import socket

logger = logging.getLogger(__name__)
lock = threading.RLock()


class Sever:
    def __init__(self, address, port, timeout=5):
        self.s = socket.socket()
        self.ip = address
        self.port = port
        self.s.settimeout(timeout)
        self.connect()

    def connect(self):
        result = False, None
        self.s.connect((self.ip, self.port))
        ret = self.s.recv(1024).decode()
        if "success" in ret:
            result = True, ret
        return result

    def send(self, context):
        with lock:
            self.s.send(str.encode(f"{context}\n"))
            logger.debug(f"send robot:{context}")
            ret = self.__read_till(5)
            logger.debug(f"recv robot:{ret}")
        return ret

    def __read_till(self, timeout):
        st = time.time()
        context = ''
        while time.time() - st < timeout:
            time.sleep(0.1)
            try:
                ret = self.s.recv(1024).decode()
                context += ret
                if ("error_order" not in context) and ("@_@" in context):
                    data = ret.split('@_@')[0].strip()
                    return True, data
            except BaseException as e:
                return False, f"controller recv timeout!!!{e}"
        return False, f"can not find EOF:@_@-->return context:{context}"

    def __del__(self):
        self.s.close()


Controller = Sever("127.0.0.1", 8080, 5)
