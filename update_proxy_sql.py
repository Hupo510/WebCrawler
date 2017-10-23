import asyncio
import aiohttp
import time
import orm
import sys
from orm import Model, StringField, BooleanField, IntegerField
from scrapy import Selector
import pymysql
import traceback
import random


class Proxy(Model):
    ''' 代理数据对象类 '''
    __table__ = 'proxy'
    url = StringField(primary_key=True, ddl='varchar(30)')
    ip = StringField(ddl='varchar(15)')
    port = StringField(ddl='varchar(5)')
    address = StringField(ddl='varchar(25)')
    types = StringField(ddl='varchar(5)')
    speed = BooleanField(default=1.0)
    response_time = BooleanField(default=1.0)
    success_times = IntegerField(default=0)
    failure_times = IntegerField(default=0)
    source_url = StringField(ddl='varchar(255)')
    verification_time = BooleanField(default=0.0)


class Crawler_Proxy:
    ''' 爬取免费代理类 '''

    def __init__(self, page_num=10, task_num=10):
        self.loop = asyncio.get_event_loop()
        self.page_num = page_num  # 爬取页数
        self.task_num = task_num  # 协程数
        self.session = aiohttp.ClientSession(loop=self.loop)  # 接口异步http请求
        self.proxy_queue = asyncio.Queue(maxsize=100, loop=self.loop)  # 文件队列
        self.succeed_times, self.failed_times = 0, 0

    async def get_content(self, url, list_xpath, ip_xpath, port_xpath, address_xpath, type_xpath):
        ''' 获取内容 '''
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
        try:
            async with self.session.get(url, headers=headers, timeout=10) as response:
                content = await response.text()
                sel = Selector(text=content)
                lis = sel.xpath(list_xpath)
                for i in lis:
                    ip = i.xpath(ip_xpath).extract_first()
                    port = i.xpath(port_xpath).extract_first()
                    address = i.xpath(address_xpath).extract_first()
                    types = i.xpath(type_xpath).extract_first()
                    if not types is None:
                        types = types.lower()
                    data = {'ip': ip, 'port': port,
                            'address': address, 'types': types, 'source_url': url}
                    # print(data)
                    await self.proxy_queue.put(data)
        except aiohttp.ClientError:
            pass  # traceback.print_exc()

    async def veri_proxy(self, proxy_url, url='http://httpbin.org/get?show_env=1', timeout=4):
        ''' 验证代理IP质量 '''
        headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        try:
            async with aiohttp.ClientSession(loop=self.loop) as session:
                start = time.time()
                async with session.get(url, proxy=proxy_url, headers=headers, timeout=timeout) as response:
                    content = await response.text()
                    end = time.time()
                    if response.status == 200:
                        return end - start
                    return content
        except Exception:
            pass  # traceback.print_exc()

    async def work_verification(self):
        ''' 验证代理IP '''
        try:
            while True:
                data = await self.proxy_queue.get()
                proxy_url = 'http://' + \
                    data['ip'] + ':' + data['port']
                response_time = await self.veri_proxy(proxy_url)
                if isinstance(response_time, float) and response_time < 1.8:
                    try:
                        pro = Proxy(url=proxy_url, ip=data['ip'], port=data['port'],
                                    address=data['address'], types=data['types'],
                                    source_url=data['source_url'],
                                    response_time=response_time, verification_time=time.time())
                        await pro.save()
                        # print(proxy_url, response_time, 'succeed!')
                        self.succeed_times += 1
                    except pymysql.err.IntegrityError:
                        pass  # traceback.print_exc()
                else:
                    # print(proxy_url, 'failed!')
                    self.failed_times += 1
                self.proxy_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def work_print(self):
        ''' 打印执行进度 '''
        try:
            run_chars = ['-', '\\', '/']
            while True:
                for char in run_chars:
                    sys.stdout.write('\rsucceed:%d / failed:%d %s' %
                                     (self.succeed_times, self.failed_times, char))
                    sys.stdout.flush()
                    await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            pass

    async def work_xici(self):
        ''' 国内高匿代理IP '''
        list_xpath = '//table[@id="ip_list"]//tr[position()>1]'
        ip_xpath = 'td[position()=2]/text()'
        port_xpath = 'td[position()=3]/text()'
        address_xpath = 'td[position()=4]/a/text()'
        type_xpath = 'td[position()=6]/text()'
        for i in range(self.page_num):
            url = 'http://www.xicidaili.com/nn/' + str(i + 1)
            await self.get_content(url, list_xpath, ip_xpath,
                                   port_xpath, address_xpath, type_xpath)

    async def work_66ip(self):
        ''' 广州代理IP 66免费代理网 '''
        list_xpath = '/html/body/div[last()]//table//tr[position()>1]'
        ip_xpath = 'td[1]/text()'
        port_xpath = 'td[2]/text()'
        address_xpath = 'td[3]/text()'
        type_xpath = 'None'
        for i in range(self.page_num):
            url = 'http://www.66ip.cn/areaindex_19/' + str(i + 1) + '.html'
            await self.get_content(url, list_xpath, ip_xpath, port_xpath,
                                   address_xpath, type_xpath)

    async def work_mimi(self):
        ''' 秘密代理IP '''
        list_xpath = '//table[@class="list"]//tr[position()>1]'
        ip_xpath = 'td[1]/text()'
        port_xpath = 'td[2]/text()'
        address_xpath = 'td[3]/a/text()'
        type_xpath = 'td[5]/text()'
        for i in range(self.page_num):
            url = 'http://www.mimiip.com/gngao/' + str(i + 1)
            await self.get_content(url, list_xpath, ip_xpath, port_xpath,
                                   address_xpath, type_xpath)

    async def work_kuai(self):
        ''' 快代理IP '''
        list_xpath = '//table[@class="table table-bordered table-striped"]/tbody/tr'
        ip_xpath = 'td[@data-title="IP"]/text()'
        port_xpath = 'td[@data-title="PORT"]/text()'
        address_xpath = 'td[@data-title="位置"]/text()'
        type_xpath = 'td[@data-title="类型"]/text()'
        for i in range(self.page_num):
            url = 'http://www.kuaidaili.com/free/inha/' + str(i + 1)
            await self.get_content(url, list_xpath, ip_xpath, port_xpath,
                                   address_xpath, type_xpath)

    async def run(self):
        ''' 运行任务 '''
        print('<<<<<<<<<<<<<<<<<<<<开始抓取代理IP>>>>>>>>>>>>>>>>>>>>')
        await orm.create_pool(self.loop, user='root', password='hupo0-0', db='web_crawler')
        task_works = [self.work_print(), self.work_66ip(), self.work_xici(),
                      self.work_mimi(), self.work_kuai()]
        workers_crawler = [asyncio.Task(task, loop=self.loop)
                           for task in task_works]
        while self.proxy_queue.qsize() == 0:  # 等待队列中存在数据
            await asyncio.sleep(0.1)
        workers_proxy = [asyncio.Task(self.work_verification(), loop=self.loop)
                         for _ in range(self.task_num)]
        await self.proxy_queue.join()
        for wp in workers_proxy:
            wp.cancel()
        for wc in workers_crawler:
            wc.cancel()
        print('\n<<<<<<<<<<<<<<<<<<<<抓取代理IP完成>>>>>>>>>>>>>>>>>>>>')


proxy = Crawler_Proxy(page_num=5, task_num=36)
loop = proxy.loop
loop.run_until_complete(proxy.run())
loop.close()
