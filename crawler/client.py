# -*- coding: utf-8 -*-

import urllib2
import icu
import random
import string


class Client(object):

    """Summary of class here.
        HTTP类

    Attributes:
        host:爬取域名
    """

    def __init__(self, host='xueqiu.com'):
        self.__host = host
        self.__agent_list = ['Mozilla/5.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0',
                             'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0'
                             ]

    def __del__(self):
        pass

    def creat_cookie(self):
        cookie = 'xq_a_token=19f5e0044f535b6b1446bb8ae1da980a48bbe850; '\
                + 'xq_a_token.sig=aaTVFAX9sVcWtOiu-5L8dL-p40k;  '\
                + 'xq_r_token=6d30415b5f855c12fd74c6e2fb7662ea40272056;  '\
                + 'xq_r_token.sig=rEvIjgpbifr6Q_Cxwx7bjvarJG0; '\

        u = string.join(random.sample({'0', '1', '2', '3', '4', '5', \
                                       '6', '7', '8', '9', '0', '1', \
                                       '2', '3', '5', '4', '6', '7', \
                                       '8', '9'}, 10)).replace(" ", "")

        ut = string.join(random.sample({'0', '1', '2', '3', '4', '5', \
                                       '6', '7', '8', '9', '0', '1', \
                                       '2', '3', '5', '4', '6', '7', \
                                       '8', '9'}, 5)).replace(" ", "")
        
        u = u + ut

        s = string.join(random.sample(['a', 'b', 'c', 'd', 'e', 'f',\
                                       'g', 'h', 'i', 'j', 'k', 'l',\
                                       'm', 'n', 'o', 'p', 'q', 'r',\
                                       's', 't', 'u', 'v', 'w', 'x',\
                                       'y', 'z', '0', '1', '2', '3',\
                                       '4', '5', '6', '7', '8', '9'], 10)).replace(" ", "")

        return cookie + 's=' + s + ";u=" + u + ";"

        # return cookie

    def request(self, url):
        header = {
            'Host': self.__host,
            'User-Agent': self.__agent_list[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': self.creat_cookie()
        }

        request = urllib2.Request(url, headers=header)
        response = urllib2.urlopen(request)
        return response.read()
    

if __name__ == "__main__":
    client = Client('xueqiu.com')
    print client.request('https://xueqiu.com/stock/f10/bizunittrdinfo.json?date=20170105')
    # print client.creat_cookie()
    # html = client.request('http://data.10jqka.com.cn/ifmarket/lhbyyb/type/1/tab/sbcs/field/sbcs/sort/desc/page/1/')
    # detector = icu.CharsetDetector()
    # detector.setText(html)
    # match = detector.detect()

    # print (match.getName())

    # print (html.decode(match.getName()))
