import selectors
import socket
import os
import re

host = 'www.2baob.com'
start_url = '/booktxt/25552/'
sel = selectors.DefaultSelector()
# save_dir = f'{os.path.dirname(__file__)}/回到明朝当王爷_generators'
# chapter_count = None
# saved_count = 0
finished = False


# if not os.path.exists(save_dir):
#     os.mkdir(save_dir)


class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_done_callback(self, fn):
        self._callbacks.append(fn)

    def set_result(self, result):
        self.result = result
        for fn in self._callbacks:
            fn(self)


class Fetcher:
    def __init__(self, url):
        self.url = url
        self.response = b''

    def fetch(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        try:
            sock.connect((host, 80))
        except BlockingIOError as e:
            pass

        f = Future()

        # 这里通过闭包，使得回调函数可以访问到在上面定义的Future对象
        def on_connected():
            f.set_result(None)

        sel.register(sock, selectors.EVENT_WRITE, on_connected)

        # 将future传递回Task.step(从而将Task.step绑定到该future的_callbacks上,
        # 使得on_connected调用set_result后能重新返回这里)
        yield f
        sel.unregister(sock)
        print('connected!')
        request = f'GET {self.url} HTTP/1.0\r\nHost: {host}\r\n\r\n'.encode('ascii')
        sock.send(request)

        while True:
            f = Future()

            def on_readable():
                f.set_result(sock.recv(4096))

            sel.register(sock, selectors.EVENT_READ, on_readable)
            # 除了上面future的功能，还将回调函数读取的内容传递回来
            chunk = yield f
            sel.unregister(sock)
            if chunk:
                self.response += chunk
            else:
                break
        self.show()

    def show(self):
        print('-------------show start---------------')
        print(self.response.decode('gbk'))
        print('-------------show end---------------')


class Task:
    def __init__(self, coro):
        self.coro = coro
        f = Future()
        f.set_result(None)
        self.step(f)

    def step(self, future):
        try:
            next_future = self.coro.send(future.result)
        except StopIteration:
            return
        next_future.add_done_callback(self.step)


def loop():
    while True:
        for key, events in sel.select():
            callback = key.data
            callback()
        if finished:
            print('[Done]')
            break


if __name__ == '__main__':
    fetcher = Fetcher(start_url)
    Task(fetcher.fetch())
    loop()
