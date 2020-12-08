import selectors
import socket
import os
import re

host = 'www.2baob.com'
start_url = '/booktxt/25552/'
sel = selectors.DefaultSelector()
save_dir = f'{os.path.dirname(__file__)}/回到明朝当王爷_generators'
chapter_count = None
saved_count = 0
finished = False

if not os.path.exists(save_dir):
    os.mkdir(save_dir)


class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def __iter__(self):
        yield self
        return self.result

    def add_done_callback(self, fn):
        self._callbacks.append(fn)

    def set_result(self, result):
        self.result = result
        for fn in self._callbacks:
            fn(self)


def read(sock):
    f = Future()

    def on_readable():
        f.set_result(sock.recv(4096))

    sel.register(sock.fileno(), selectors.EVENT_READ, on_readable)
    chunk = yield from f  # Read one chunk.
    sel.unregister(sock.fileno())
    return chunk


def read_all(sock):
    response = []
    # Read whole response.
    chunk = yield from read(sock)
    while chunk:
        response.append(chunk)
        chunk = yield from read(sock)

    return b''.join(response)


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

        def on_connected():
            f.set_result(None)

        sel.register(sock, selectors.EVENT_WRITE, on_connected)
        yield from f
        sel.unregister(sock)
        request = f'GET {self.url} HTTP/1.0\r\nHost: {host}\r\n\r\n'.encode('ascii')
        sock.send(request)
        self.response = yield from read_all(sock)

        if self.url == start_url:
            self.parse_links()
        else:
            self.save()

    def parse_links(self):
        global chapter_count
        text = self.response.decode('gbk')
        urls = re.findall(rf'{start_url}\d+.html', text)
        chapter_count = len(urls)
        for url in urls:
            coro = Fetcher(url).fetch()
            Task(coro)

    def save(self):
        global saved_count, finished
        filename = self.url.split('/')[-1]
        filepath = os.path.join(save_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(self.response)
        saved_count += 1
        print(f'[{saved_count}/{chapter_count}]Saved {filepath}.')
        if saved_count == chapter_count:
            finished = True


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
