import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import time
import orm
import uuid
import sys
from orm import Model, StringField, BooleanField, FloatField, TextField
import pymysql as mdb
import random


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


class Topic(Model):
    __table__ = 'topic'
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    imgurl = TextField()
    title = StringField(ddl='varchar(255)')
    created_at = FloatField(default=time.time)


class Crawler:
    def __init__(self, url_base, ip_list, page_task_num=3, topic_task_num=10):
        '''初始化爬虫'''
        self.loop = asyncio.get_event_loop()
        self.max_tries = len(ip_list)  # 每个请求重试次数
        self.page_task_num = page_task_num  # 主页请求协程数
        self.topic_task_num = topic_task_num  # 话题请求协程数
        self.page_queue = asyncio.Queue(maxsize=10, loop=self.loop)  # 主页队列
        self.topic_queue = asyncio.Queue(maxsize=100, loop=self.loop)  # 话题队列
        self.url_base = url_base  # 首地址
        self.ip_list = ip_list  # 代理IP列表
        self.topic_num = 0

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

    async def handle_page(self, url):
        ''' 处理主页请求 '''
        page = await self.get_html(url)
        body = BeautifulSoup(page, 'lxml')
        divs = body.find_all('div', attrs={'class': 'aw-question-content'})
        for d in divs:  # 解析话题页链接
            h4 = d.find('h4')
            if not h4 is None:
                a = h4.find('a', attrs={'class': 'atitle'})
                if not a is None:
                    if a.has_attr('href'):
                        href = a['href']
                        await self.topic_queue.put(href)
        try:  # 获取下一页
            control = body.find('div', attrs={'class': 'page-control'})
            lias = control.find_all('a')
            for a in lias:
                if not a.string is None:
                    if a.string == '>':
                        nextPage = a['href']
                        await self.page_queue.put(nextPage)
        except:
            print('get next page error!')

    async def handle_topic(self, url):
        ''' 处理话题请求 '''
        page = await self.get_html(url)
        body = BeautifulSoup(page, 'lxml')
        divs = body.find_all('div', attrs={'class': 'Mid2L_con'})
        for div in divs:  # 解析文件
            ps = div.find_all('p')
            for p in ps:
                title = p.get_text()
                img = p.find('img')
                if not img is None:
                    if img.has_attr('data-original'):
                        imgUrl = img['data-original']
                    elif img.has_attr('src'):
                        imgUrl = img['src']
                    else:
                        imgUrl = None
                    if not imgUrl is None:
                        self.topic_num = self.topic_num + 1
                        info = '\r' + '获取到' + str(self.topic_num) + '条记录！'
                        sys.stdout.write(info)
                        sys.stdout.flush()
                        topic = Topic(imgurl=imgUrl, title=title)
                        await topic.save()
                        if self.topic_num % 2 == 0:
                            sys.stdout.write('/')
                        else:
                            sys.stdout.write('\\')
                        sys.stdout.flush()

    async def get_html(self, url):
        ''' 获取网页内容 '''
        # print('读取%s' % url)
        # USER_AGENTS 随机头信息,用来突破爬取网站的反爬虫
        USER_AGENTS = [
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
            "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
            "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
            "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
        ]
        headers = {
            # 'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
            'User-Agent': random.choice(USER_AGENTS)}
        proxy = 'http://' + random.choice(self.ip_list)
        # print('使用代理：' + proxy)
        tries = 0
        while tries < self.max_tries:
            try:
                async with aiohttp.ClientSession(loop=self.loop) as session:
                    async with session.get(url, headers=headers, timeout=60) as response:
                        content = await response.text()
                        return content
            except Exception:
                pass
            tries += 1
        print('%s 请求超次！' % url)

    async def run(self):
        ''' 运行任务 '''
        await orm.create_pool(loop, user='root', password='hupo0-0', db='fuliqu')
        # print(await Topic.findAll())
        self.page_queue.put_nowait(self.url_base)  # 起始地址入队列
        workers_page = [asyncio.Task(self.work_page(), loop=self.loop)
                        for _ in range(self.page_task_num)]
        workers_tupic = [asyncio.Task(self.work_topic(), loop=self.loop)
                         for _ in range(self.topic_task_num)]
        await self.page_queue.join()
        await self.topic_queue.join()
        for wp in workers_page:
            wp.cancel()
        for wt in workers_tupic:
            wt.cancel()


def get_valid_iplist():
    conn = mdb.connect('localhost', 'root', 'hupo0-0', 'proxies')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT content FROM %s' % 'valid_ip')
        result = cursor.fetchall()
        ip_list = []
        for i in result:
            ip_list.append(i[0])
        return ip_list
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


ip_list = get_valid_iplist()
print('代理IP地址池：\n', ip_list)
crawler = Crawler('http://www.fuliqu.com/', ip_list=ip_list)
loop = crawler.loop
loop.run_until_complete(crawler.run())
loop.close()
