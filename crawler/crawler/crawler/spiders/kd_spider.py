# -*- coding: utf-8 -*-
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
import scrapy
from scrapy.http import Request


class KDSpider(scrapy.Spider):

    SIGNAL_CRAWL_SUCCESSED = object()
    SIGNAL_CRAWL_FAILED = object()
    name = 'SingleSpider'
    start_urls = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(KDSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.signal_dispatcher, signals.spider_opened)
        crawler.signals.connect(spider.signal_dispatcher, signals.spider_idle)
        crawler.signals.connect(spider.signal_dispatcher, signals.spider_error)
        return spider

    def __init__(self, callback=None):
        super(KDSpider, self).__init__()
        self.signals_callback = callback

    def signal_dispatcher(self, signal):
        if self.signals_callback:
            if signal == signals.spider_idle or signal == signals.spider_error:
                raise DontCloseSpider('I prefer live spiders')
            elif signal == signals.spider_opened:
                self.signals_callback(signal, spider=self)

    def add_task(self, task, is_retry=False, times=1):
        if not is_retry:
            print('Add New Task: ' + task['url'])

        req = Request(task['url'],
                      method=task['method'],
                      headers=task['headers'],
                      callback=self.parse,
                      dont_filter=True,
                      errback=self.req_err)

        self.crawler.engine.schedule(req, self)

    def req_err(self, response):
        print (response)

    def parse(self, response):
        self.signals_callback(KDSpider.SIGNAL_CRAWL_SUCCESSED,
                              data=response.body)
