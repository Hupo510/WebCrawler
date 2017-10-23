try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except ImportError:
    pass
import requests
requests.adapters.DEFAULT_RETRIES = 5
from bs4 import BeautifulSoup
import gevent
from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool
import re
import os
import sys
import pprint
import random
import asyncio
import aiohttp
# from multiprocessing.pool import Pool
# from multiprocessing import cpu_count
from multiprocessing.dummy import Pool as ThreadPool


def header_making():
    header = {'User-Agent': 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
              'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'}
    return header
##
# list all filename in path
##


def Get_filelist(path):
    for home, dirs, files in os.walk(path):
        for filename in files:
            yield os.path.join(home, filename)
##
# download picture
##


def pic_download(path, url, targetDir='D:\\spiderdown4'):
    if not os.path.isdir(targetDir):
        os.mkdir(targetDir)
    pic_dir = os.path.join(targetDir, path)
    try:
        header = header_making()
        header['Referer'] = url
        r = requests.Session()
        r.keep_alive = False
        image = r.get(url, stream=True, headers=header, timeout=60)
        if image.status_code == 200:
            image = image.content
            with open(pic_dir, 'wb') as img:
                img.write(image)
                img.close()
                return
        else:
            print('download failed')
            return
    except:
        print("failed!!!")
        header = header_making()
        header['Referer'] = url
        r = requests.Session()
        r.keep_alive = False
        image = r.get(url, stream=True, headers=header, timeout=60)
        image = image.content
        with open(pic_dir, 'wb') as img:
            img.write(image)
            img.close()
            return


##
# fetch HTML
##
def fetch_content(url):
    header = header_making()
    header['Referer'] = url
    r = requests.Session()
    r.keep_alive = False
    return r.get(url, headers=header, timeout=60).text
##
# to find the biggest name
##


def File_naming(path='D:\\spiderdown4'):
    return max([int(i.split("\\")[-1].split('.')[0]) for i in Get_filelist(path)] or [1])

##
# parse HTML
##


def parse(url):
    print('start')
    soup = BeautifulSoup(fetch_content(url), "html.parser")
    fetch_list = []
    result = []

    fetch_list = ["http://cl.gv8.xyz/" + i.get("href") for i in soup.find_all(
        "a", href=re.compile("htm_data.*?html"), id="")]
    # for link in soup.find_all("a", href=re.compile("htm_data.*?html"), id=""):
    #     fetch_list.append('http://cc.uqsk.org/'+link.get("href"))
    # de-duplicated for fetch_list
    fetch_list = sorted(set(fetch_list), key=fetch_list.index)
    jobs = [gevent.spawn(fetch_content, url) for url in fetch_list]
    gevent.joinall(jobs)

    for page in [job.value for job in jobs]:
        soupChild = BeautifulSoup(page, "html.parser")
        [result.append(linkchild.get("src")) for linkchild in soupChild.findAll(
            "input", type="image", src=re.compile("https://.*?\.jpg"))]

    # de-duplicated for fetch_list
    result = sorted(set(result), key=result.index)
    jobs = [gevent.spawn(pic_download, str(index + File_naming()) + '.jpg', url)
            for index, url in enumerate(result)]
    gevent.joinall(jobs)

    return


if __name__ == '__main__':
    from time import time
    start = time()
    # p = Pool(2)
    p = ThreadPool(2)
    p.map(parse, ["http://cl.gv8.xyz/thread0806.php?fid=16&search=&page=" + str(i)
                  for i in range(1, 9)])
    p.close()
    p.join()
    end = time()
    print(end - start)
