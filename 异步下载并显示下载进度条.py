import asyncio
import aiohttp
import aiofiles
import sys
import time


async def aio_download(loop, url):
    ''' 异步同步请求与保存 '''
    session = aiohttp.ClientSession(loop=loop)
    async with session.get(url, timeout=60) as response:
        content_size = int(response.headers['content-length'])  # 内容体总大小
        print('总大小：%d Byte' % content_size)
        async with aiofiles.open('1.gif', 'wb') as f:
            data_size = 0
            while True:
                chunk = await response.content.read(2**10)
                if chunk:
                    await f.write(chunk)
                    data_size = data_size + len(chunk)
                    percent = data_size / content_size
                    max_arrow = 50
                    num_arrow = int(percent * max_arrow)  # 计算显示多少个'>'
                    num_line = max_arrow - num_arrow  # 计算显示多少个'-'
                    process_bar = '\r' + '%.2f/%.2f MB' % ((data_size / (2**20)), (content_size / (2**20))) + '[' + '>' * num_arrow + '-' * num_line + ']' + '%.2f' % (
                        percent * 100) + '%'  # 带输出的字符串，'\r'表示不换行回到最左边
                    sys.stdout.write(process_bar)
                    sys.stdout.flush()
                else:
                    sys.stdout.write(' 下载完成!\n')
                    sys.stdout.flush()
                    break
    session.close()


loop = asyncio.get_event_loop()
task = aio_download(
    loop, 'http://wx2.sinaimg.cn/mw690/6adc108fly1fkjy58lyf1g20c006px6r.gif')
loop.run_until_complete(task)
loop.close()
print('下载任务完成！')
time.sleep(5)
