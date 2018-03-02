# -*- coding: utf-8 -*-


import threading
import time
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.kd_spider import KDSpider
from twisted.internet import reactor

import random
import string

settings = get_project_settings()
crawler_process = CrawlerProcess(settings)
crawler_process.join()


class KDCrawler(threading.Thread):
    def __init__(self):
        super(KDCrawler, self).__init__()
        threading.Thread.__init__(self, name='crawler')
        self.setDaemon(True)
        print('Spider Is Starting.')
        self.spider = None
        self.spider_mqs = None
        self.signals_list = {
            signals.spider_opened: self.spider_opened,
            KDSpider.SIGNAL_CRAWL_SUCCESSED: self.crawl_successed,
            KDSpider.SIGNAL_CRAWL_FAILED: self.crawl_failed
        }
        self.process = crawler_process
        self.process.crawl(KDSpider, callback=self.spider_signals)

        self.__task_list = []

    def spider_opened(self, spider):
        if not self.spider:
            self.spider = spider
            self.spider_mqs = spider.crawler.engine.slot.scheduler.mqs
            print('Spider Was Ready')

    def crawl_successed(self, data):
        print (data)

    def crawl_failed(self, status):
        print (status)

    def add_task(self, url):
        self.__task_list.append(url)

    def spider_signals(self, signal, *args, **kwargs):
        if signal not in self.signals_list.keys():
            return
        func = self.signals_list.get(signal, None)
        if func:
            func(*args, **kwargs)

    def add_task(self, task):
        self.__task_list.append(task)
        self.exec_task()

    def exec_task(self):
        while len(self.__task_list):
            if self.spider.crawler.engine.slot.scheduler.mqs.queues:
                mqs = self.spider.crawler.engine.slot.scheduler.mqs.queues.get(0, None)
                if mqs and len(mqs.q) > 299:
                    time.sleep(3)
                    return
            if not self.spider:
                continue

            task = self.__task_list.pop(0)
            self.spider.add_task(task)


def creat_cookie():
    cookie = 'xq_a_token=5c915d14d91dc74b5f2e4c3b4753137ae66c1926; ' \
             + 'xq_a_token.sig=CGCHkBovlWaQtWbwukG6L3FRNIA;  ' \
             + 'xq_r_token=e796a61232e2cf0d90d560d30af22b227d8f7eeb; ' \
             + 'xq_r_token.sig=VeCkcFeNm3Vszkg9DbEZW9Pg0pA;' \

    u = string.join(random.sample({'0', '1', '2', '3', '4', '5', \
                                   '6', '7', '8', '9', '0', '1', \
                                   '2', '3', '5', '4', '6', '7', \
                                   '8', '9'}, 10)).replace(" ", "")

    ut = string.join(random.sample({'0', '1', '2', '3', '4', '5', \
                                    '6', '7', '8', '9', '0', '1', \
                                    '2', '3', '5', '4', '6', '7', \
                                    '8', '9'}, 5)).replace(" ", "")

    u = u + ut

    s = string.join(random.sample(['a', 'b', 'c', 'd', 'e', 'f', \
                                   'g', 'h', 'i', 'j', 'k', 'l', \
                                   'm', 'n', 'o', 'p', 'q', 'r', \
                                   's', 't', 'u', 'v', 'w', 'x', \
                                   'y', 'z', '0', '1', '2', '3', \
                                   '4', '5', '6', '7', '8', '9'], 10)).replace(" ", "")

    return cookie + 's=' + s + ";u=" + u + ";"


if __name__ == "__main__":
    reactor.__init__()
    crawler = KDCrawler()
    task = {'method': 'GET', 'url': 'https://xueqiu.com/stock/f10/bizunittrdinfo.json?date=20170105', 'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        # 'Referer': 'https://xueqiu.com',
        'Cookie': creat_cookie()}}
    crawler.add_task(task)
    reactor.run()
