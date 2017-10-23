import asyncio
import requests
import os
import aiohttp
import aiofiles


async def download(loop, url):
    ''' 同步请求与保存 '''
    with requests.get(url, stream=True) as response:
        chunk_size = 1024  # 单次请求最大值
        content_size = int(response.headers['content-length'])  # 内容体总大小
        print('总大小：%d Byte' % content_size)
        with open('1.gif', 'wb') as f:
            for data in response.iter_content(chunk_size=chunk_size):
                f.write(data)
                print('+', end='')


async def aio_download(loop, url):
    ''' 异步同步请求与保存 '''
    session = aiohttp.ClientSession(loop=loop)
    async with session.get(url, timeout=60) as response:
        content_size = int(response.headers['content-length'])  # 内容体总大小
        print('总大小：%d Byte' % content_size)
        chunk_size = 1024  # 单次请求最大值
        async with aiofiles.open('2.gif', 'wb') as f:
            while True:
                chunk = await response.content.read(chunk_size)
                if not chunk:
                    print('下载完成！')
                    break
                else:
                    print('-', end='')
                    await f.write(chunk)
                    
    session.close()


loop = asyncio.get_event_loop()
task = aio_download(
    loop, 'http://wx2.sinaimg.cn/mw690/6adc108fly1fkjy58lyf1g20c006px6r.gif')
loop.run_until_complete(task)
loop.close()
