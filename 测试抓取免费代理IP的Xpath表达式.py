import requests
import traceback
from scrapy import Selector


def get_content(url, list_xpath, ip_xpath, port_xpath, address_xpath, type_xpath, encoding=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
    results = requests.get(url, headers=headers, timeout=10)
    if not encoding is None:
        results.encoding = encoding
    sel = Selector(results)
    lis = sel.xpath(list_xpath)
    for i in lis:
        ip = i.xpath(ip_xpath).extract_first()
        port = i.xpath(port_xpath).extract_first()
        address = i.xpath(address_xpath).extract_first()
        types = i.xpath(type_xpath).extract_first()
        if types is None:
            types = 'http'
        data = {'ip': ip, 'port': port,
                'address': address, 'types': types.lower()}
        print(data)


list_xpath = '/html/body/div[last()]//table//tr[position()>1]'
ip_xpath = 'td[1]/text()'
port_xpath = 'td[2]/text()'
address_xpath = 'td[3]/text()'
type_xpath = 'None'
url = 'http://www.66ip.cn/areaindex_19/1.html'
get_content(url, list_xpath, ip_xpath, port_xpath,
            address_xpath, type_xpath, encoding='GBK')
print('end')

''' list_xpath = '//table[@class="list"]//tr[position()>1]'
ip_xpath = 'td[1]/text()'
port_xpath = 'td[2]/text()'
address_xpath = 'td[3]/a/text()'
type_xpath = 'td[5]/text()'
url = 'http://www.mimiip.com/gngao/1'
get_content(url, list_xpath, ip_xpath, port_xpath,
            address_xpath, type_xpath) '''

''' list_xpath = '//table[@class="table table-bordered table-striped"]/tbody/tr'
ip_xpath = 'td[@data-title="IP"]/text()'
port_xpath = 'td[@data-title="PORT"]/text()'
address_xpath = 'td[@data-title="位置"]/text()'
type_xpath = 'td[@data-title="类型"]/text()'
url = 'http://www.kuaidaili.com/free/inha/1'
get_content(url, list_xpath, ip_xpath, port_xpath,
            address_xpath, type_xpath) '''
