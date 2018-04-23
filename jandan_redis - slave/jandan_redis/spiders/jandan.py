# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis.spiders import RedisCrawlSpider
from jandan_redis.items import JandanRedisItem

class JandanSpider(RedisCrawlSpider):
    name = 'jandan'

    redis_key = 'jandan:start_urls'

    def __init__(self, *args, **kwargs):
        super(JandanSpider, self).__init__(*args, **kwargs)
        self.page = 2

    def parse(self, response):
        colums = response.xpath('//*[@id="content"]/div/div/div/h2/a')
        for colum in colums:
            item = JandanRedisItem()
            item['title'] = colum.xpath('text()').extract_first()
            item['title_url'] = colum.xpath('@href').extract_first()
            yield item
        self.page += 1
        next_url = 'http://jandan.net/page/%d' % self.page
        yield scrapy.Request(next_url)
        pass
