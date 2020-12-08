import asyncio
import aiohttp
import os
import re

start_url = '/booktxt/25552/'
save_dir = f'{os.path.dirname(__file__)}/回到明朝当王爷_asyncio'
chapter_count = None
saved_count = 0
finished = False
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

start_url = 'http://www.2baob.com/booktxt/25552/'


class Fetcher:
    def __init__(self):
        self.session = None
        asyncio.gather(self.init_session())

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def fetch(self, url):
        resp = await self.session.get(url)
        body = await resp.read()

        if url == start_url:
            text = body.decode('gbk')
            await self.parse_links(text)
            await self.session.close()
        else:
            self.save(url, body)

    async def parse_links(self, text):
        global chapter_count
        urls = re.findall(rf'/booktxt/25552/\d+.html', text)
        urls = ['http://www.2baob.com' + url for url in urls]
        print(urls)
        chapter_count = len(urls)
        await asyncio.gather(*[self.fetch(url) for url in urls])

    def save(self, url, content):
        global saved_count, finished
        filename = url.split('/')[-1]
        filepath = os.path.join(save_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        saved_count += 1
        print(f'[{saved_count}/{chapter_count}]Saved {filepath}.')
        if saved_count == chapter_count:
            finished = True


loop = asyncio.get_event_loop()
loop.run_until_complete(Fetcher().fetch(start_url))
