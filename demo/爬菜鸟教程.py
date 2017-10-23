from bs4 import BeautifulSoup as bs
import asyncio
import aiohttp
import time


async def getPage(url, res_list, callback=None):
    print(url)
    headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    sem = asyncio.Semaphore(2)  # 限制同时运行协程数量
    with (await sem):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                print(resp.status)
                # 断言，判断网站状态
                assert resp.status == 200
                # 判断不同回调函数做处理
                if callback == grabDesign:
                    body = await resp.text()
                    callback(res_list, body)
                else:
                    return await resp.text()
                # 关闭请求
                session.close()


def grabDesign(res_list, body):
    page = bs(body, "lxml")
    articles = page.find_all(
        'div', attrs={'class': 'design'})
    print(articles)
    designs = articles[0].find_all('a')
    for a in designs:
        x = a['href']
        res_list.append('http://www.runoob.com' + x)


start = time.time()
page_url_base = 'http://www.runoob.com/python/'
loop = asyncio.get_event_loop()
ret_list = list()
tasks = getPage(page_url_base, ret_list, callback=grabDesign)
loop.run_until_complete(tasks)
loop.close()
print("Elapsed Time: %s" % (time.time() - start))
print(ret_list)
