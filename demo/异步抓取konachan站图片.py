import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import time
import os


class Crawler:
    def __init__(self, url_base, page_task_num=1, topic_task_num=3, file_task_num=9):
        '''初始化爬虫'''
        self.loop = asyncio.get_event_loop()
        self.max_tries = 3  # 每个请求重试次数
        self.page_task_num = page_task_num  # 主页请求协程数
        self.topic_task_num = topic_task_num  # 话题请求协程数
        self.file_task_num = file_task_num  # 文件请求协程数
        self.page_queue = asyncio.Queue(maxsize=2, loop=self.loop)  # 主页队列
        self.topic_queue = asyncio.Queue(maxsize=6, loop=self.loop)  # 话题队列
        self.file_queue = asyncio.Queue(maxsize=36, loop=self.loop)  # 文件队列
        self.session = aiohttp.ClientSession(loop=self.loop)  # 接口异步http请求
        self.url_base = url_base  # 首地址
        self.base_path = self.create_base_path()

    def close(self):
        """回收http session"""
        self.session.close()

    def create_base_path(self,folder_name=None):
        if folder_name is None:
            folder_name = 'konachan'
        cwd = os.getcwd()
        path = cwd + '\\' + folder_name + '\\'
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    async def work_page(self):
        ''' 主页请求队列消费者 '''
        try:
            while True:
                url = await self.page_queue.get()
                await self.handle_page(url)
                self.page_queue.task_done()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print('work_page CancelledError')

    async def work_topic(self):
        ''' 话题请求队列消费者 '''
        try:
            while True:
                url = await self.topic_queue.get()
                await self.handle_topic(url)
                self.topic_queue.task_done()
                await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            print('work_topic CancelledError')

    async def work_file(self):
        ''' 文件请求队列消费者 '''
        try:
            while True:
                url = await self.file_queue.get()
                await self.handle_file(url)
                self.file_queue.task_done()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print('work_file CancelledError')

    async def handle_page(self, url):
        ''' 处理主页请求 '''
        page = await self.get_html(url)
        body = BeautifulSoup(page, 'lxml')
        acs = body.find_all('a', attrs={'class': 'thumb'})
        for a in acs:  # 解析话题页链接
            if not a is None:
                if a.has_attr('href'):
                    href = self.url_base + a['href']
                    await self.topic_queue.put(href)
        try:  # 获取下一页
            next_page = body.find('a', attrs={'class': 'next_page','rel':'next'})
            if not next_page is None:
                if next_page.has_attr('href'):
                    nextPage = self.url_base + next_page['href']
                    await self.page_queue.put(nextPage)
        except:
            print('get next page error!')

    async def handle_topic(self, url):
        ''' 处理话题请求 '''
        page = await self.get_html(url)
        body = BeautifulSoup(page, 'lxml')
        img = body.find('img', attrs={'class': 'image'})
        if not img is None:
            if img.has_attr('src'):
                imgUrl = 'http:' + img['src']
                await self.file_queue.put(imgUrl)

    async def handle_file(self, url):
        ''' 处理gif请求 '''
        await self.get_file(url)

    async def get_html(self, url):
        ''' 获取网页内容 '''
        print('读取%s' % url)
        headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        tries = 0
        while tries < self.max_tries:
            try:
                async with self.session.get(url, headers=headers, timeout=60) as response:
                    content = await response.text()
                    return content
            except aiohttp.ClientError:
                pass
            tries += 1
        print('%s 请求超次！' % url)

    async def get_file(self, url):
        ''' 获取文件 '''
        print('读取%s' % url)
        save_path = url.split('/')[-1]
        tries = 0
        while tries < self.max_tries:
            try:
                async with self.session.get(url, timeout=60) as response:
                    async with aiofiles.open(self.base_path + save_path, 'wb') as f:
                        await f.write(await response.read())
                        return
            except aiohttp.ClientError:
                pass
            tries += 1
        print('%s 请求超次！' % url)

    async def run(self):
        ''' 运行任务 '''
        self.page_queue.put_nowait(self.url_base + '/post')  # 起始地址入队列
        workers_page = [asyncio.Task(self.work_page(), loop=self.loop)
                        for _ in range(self.page_task_num)]
        workers_tupic = [asyncio.Task(self.work_topic(), loop=self.loop)
                         for _ in range(self.topic_task_num)]
        workers_file = [asyncio.Task(self.work_file(), loop=self.loop)
                        for _ in range(self.file_task_num)]
        await self.page_queue.join()
        await self.topic_queue.join()
        await self.file_queue.join()
        for wp in workers_page:
            wp.cancel()
        for wt in workers_tupic:
            wt.cancel()
        for wf in workers_file:
            wf.cancel()


crawler = Crawler('http://konachan.net')
loop = crawler.loop
loop.run_until_complete(crawler.run())
loop.close()
