import selectors
import socket
import os
import re

host = 'www.2baob.com'
start_url = '/booktxt/25552/'
sel = selectors.DefaultSelector()
save_dir = f'{os.path.dirname(__file__)}/回到明朝当王爷_callback'
chapter_count = None
saved_count = 0
finished = False
if not os.path.exists(save_dir):
    os.mkdir(save_dir)


class Fetcher:
    def __init__(self, url):
        self.response = b''
        self.url = url
        self.sock = None

    def fetch(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        try:
            self.sock.connect((host, 80))
        except BlockingIOError as e:
            pass
        sel.register(self.sock, selectors.EVENT_WRITE, self.connected)

    def connected(self, key, mask):
        sel.unregister(self.sock)
        request = f'GET {self.url} HTTP/1.0\r\nHost: {host}\r\n\r\n'.encode('ascii')
        self.sock.send(request)
        sel.register(self.sock, selectors.EVENT_READ, self.read_response)

    def read_response(self, key, mask):
        chunk = self.sock.recv(4096)
        if chunk:
            self.response += chunk
        # EOF
        else:
            sel.unregister(self.sock)
            self.sock.close()

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
            Fetcher(url).fetch()

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


def loop():
    while True:
        for key, events in sel.select():
            callback = key.data
            callback(key, events)
        if finished:
            print('[Done]')
            break


if __name__ == '__main__':
    Fetcher(start_url).fetch()
    loop()
