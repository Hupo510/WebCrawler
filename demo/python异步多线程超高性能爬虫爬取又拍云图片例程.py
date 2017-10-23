import asyncio
import base64
import os
import urllib

import aiohttp
import aiofiles

# -----------------------
# -----------------------
bucket = 'bucket_name'  # 这里就是空间名称
username = 'username'  # 操作员账号
password = 'password'  # 操作员密码
# 空间外联地址 因为又拍云的http下载没有频率限制，所以使用http下载 不适用restful的api接口下载
hostname = "http://xxxxx"

# 这里是本地保存的根路径 这样下载后路径地址就跟空间内的地址是相对的了
base_save_path = 'f:'
# -----------------------

headers = {}
auth = base64.b64encode(f'{username}:{password}'.encode(encoding='utf-8'))
headers['Authorization'] = 'Basic ' + str(auth)  # 又拍云认证header头
headers['User-Agent'] = "UPYUN_DOWNLOAD_SCRIPT"
headers['x-list-limit'] = '300'

thread_sleep = 1


def is_dic(url):
    """判断key是否是目录 根据是否有后缀名判断"""
    # print(f'判断url：{url}')
    url = url.replace('http://v0.api.upyun.com/', '')
    if len(url.split('.')) == 1:
        return True
    else:
        return False


class Crawler:
    def __init__(self, init_key, hostname, max_tasks=10, pic_tsak=50):
        '''初始化爬虫'''
        self.loop = asyncio.get_event_loop()
        self.max_tries = 4  # 每个图片重试册数
        self.max_tasks = max_tasks  # 接口请求进程数
        self.key_queue = asyncio.Queue(loop=self.loop)  # 接口队列
        self.pic_queue = asyncio.Queue(loop=self.loop)  # 图片队列
        self.session = aiohttp.ClientSession(loop=self.loop)  # 接口异步http请求
        self.key_queue.put_nowait(
            {'key': init_key, 'x-list-iter': None, 'hostname': hostname})  # 初始化接口队列 push需要下载的目录
        self.pic_tsak = pic_tsak  # 图片下载队列

    def close(self):
        """回收http session"""
        self.session.close()

    async def work(self):
        """接口请求队列消费者"""
        try:
            while True:
                url = await self.key_queue.get()
                # print('key队列数量:' + await self.key_queue.qsize())
                await self.handle(url)
                self.key_queue.task_done()
                await asyncio.sleep(thread_sleep)
        except asyncio.CancelledError:
            pass

    async def work_pic(self):
        """图片请求队列消费者"""
        try:
            while True:
                url = await self.pic_queue.get()
                await self.handle_pic(url)
                self.pic_queue.task_done()
                await asyncio.sleep(thread_sleep)
        except asyncio.CancelledError:
            pass

    async def handle_pic(self, key):
        """处理图片请求"""
        url = (lambda x: x[0] == '/' and x or '/' + x)(key['key'])
        url = url.encode('utf-8')
        url = urllib.parse.quote(url)

        pic_url = key['hostname'] + url + '!s400'

        tries = 0
        while tries < self.max_tries:
            try:
                print(f'请求图片:{pic_url}')
                async with self.session.get(pic_url, timeout=60) as response:
                    async with aiofiles.open(key['save_path'], 'wb') as f:
                        # print('保存文件:{}'.format(key['save_path']))
                        await f.write(await response.read())
                break
            except aiohttp.ClientError:
                pass
            tries += 1

    async def handle(self, key):

        """处理接口请求"""
        url = '/' + bucket + \
            (lambda x: x[0] == '/' and x or '/' + x)(key['key'])
        url = url.encode('utf-8')
        url = urllib.parse.quote(url)

        if key['x-list-iter'] is not None:
            if key['x-list-iter'] is not None or not 'g2gCZAAEbmV4dGQAA2VvZg':
                headers['X-List-Iter'] = key['x-list-iter']

        tries = 0
        while tries < self.max_tries:
            try:
                reque_url = "http://v0.api.upyun.com" + url
                print(f'请求接口:{reque_url}')
                async with self.session.get(reque_url, headers=headers, timeout=60) as response:
                    content = await response.text()
                    try:
                        iter_header = response.headers.get('x-upyun-list-iter')
                    except:
                        iter_header = 'g2gCZAAEbmV4dGQAA2VvZg'
                    list_json_param = content + "`" + \
                        str(response.status) + "`" + str(iter_header)
                    await self.do_file(self.get_list(list_json_param), key['key'], key['hostname'])
                break
            except aiohttp.ClientError:
                pass
            tries += 1

    def get_list(self, content):
        # print(content)
        if content:
            content = content.split("`")
            items = content[0].split('\n')
            content = [dict(zip(['name', 'type', 'size', 'time'], x.split('\t'))) for x in items] + content[1].split() + \
                content[2].split()
            return content
        else:
            return None

    async def do_file(self, list_json, key, hostname):
        """处理接口数据"""
        for i in list_json[:-2]:
            if not i['name']:
                continue
            new_key = key + i['name'] if key == '/' else key + '/' + i['name']
            try:
                if i['type'] == 'F':
                    self.key_queue.put_nowait(
                        {'key': new_key, 'x-list-iter': None, 'hostname': hostname})
                else:
                    try:
                        if not os.path.exists(bucket + key):
                            os.makedirs(bucket + key)
                    except OSError as e:
                        print('新建文件夹错误:' + str(e))
                    save_path = base_save_path + '/' + bucket + new_key
                    if not os.path.isfile(save_path):
                        self.pic_queue.put_nowait(
                            {'key': new_key, 'save_path': save_path, 'x-list-iter': None, 'hostname': hostname})
                    else:
                        print(f'文件已存在:{save_path}')
            except Exception as e:
                print('下载文件错误！:' + str(e))
                async with aiofiles.open('download_err.txt', 'a') as f:
                    await f.write(new_key + '\n')
        if list_json[-1] != 'g2gCZAAEbmV4dGQAA2VvZg':
            self.key_queue.put_nowait(
                {'key': key, 'x-list-iter': list_json[-1], 'hostname': hostname})

    async def run(self):
        """初始化任务进程"""
        workers = [asyncio.Task(self.work(), loop=self.loop)
                   for _ in range(self.max_tasks)]

        workers_pic = [asyncio.Task(self.work_pic(), loop=self.loop)
                       for _ in range(self.pic_tsak)]

        await self.key_queue.join()
        await self.pic_queue.join()

        workers.append(workers_pic)
        for w in workers:
            w.cancel()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    crawler = Crawler('/', hostname, max_tasks=5, pic_tsak=150)
    loop.run_until_complete(crawler.run())

    crawler.close()

    loop.close()
