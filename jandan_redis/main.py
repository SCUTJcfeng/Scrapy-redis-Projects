from scrapy.cmdline import execute
import redis

r = redis.Redis()
r.lpush('jandan:start_urls', 'http://jandan.net/page/2')
execute('scrapy crawl jandan'.split())
