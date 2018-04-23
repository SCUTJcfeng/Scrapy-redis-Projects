# Scrapy-redis学习系列

# [Scrapy-redis学习系列之一：初识scrapy-redis](https://blog.csdn.net/SCUTJcfeng/article/details/80054017)

## 一、scarpy-redis介绍
[scrapy-reids](https://github.com/rmax/scrapy-redis)官方介绍的三个特性如下：

* Distributed crawling/scraping（分布式爬虫）

You can start multiple spider instances that share a single redis queue. Best suitable for broad multi-domain crawls.
（你可以在启用多个spider实例的时候分享同一个redis队列。这对广泛多域抓取来说是最合适的。）

* Distributed post-processing（分布式后处理）

Scraped items gets pushed into a redis queued meaning that you can start as many as needed post-processing processes sharing the items queue.
（抓取的items被推入redis队列中，这意味着你可以在启用尽可能多的后处理流程的时候分享同一个items队列。）

* Scrapy plug-and-play components（Scrapy即插即用的组件）

Scheduler + Duplication Filter, Item Pipeline, Base Spiders.
（这几个组件都是用来替换Scrapy原生组件用的。）

简单来说，`scarpy-redis`就是用来在scrapy中实现分布式的组件。`scarpy-redis`的主要特性介绍完了，详细的请到`scarpy-redis`的[Github](https://github.com/rmax/scrapy-redis)主页查看。

---

## 二、最简单的scarpy-redis项目

在原Scrapy项目的基础上修改即可。

### 1. 修改`settings.py`
[Github](https://github.com/rmax/scrapy-redis)项目主页上有settings推荐，这里贴一下：

```
# Enables scheduling storing requests queue in redis.
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# Ensure all spiders share same duplicates filter through redis.
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# Default requests serializer is pickle, but it can be changed to any module
# with loads and dumps functions. Note that pickle is not compatible between
# python versions.
# Caveat: In python 3.x, the serializer must return strings keys and support
# bytes as values. Because of this reason the json or msgpack module will not
# work by default. In python 2.x there is no such issue and you can use
# 'json' or 'msgpack' as serializers.
#SCHEDULER_SERIALIZER = "scrapy_redis.picklecompat"

# Don't cleanup redis queues, allows to pause/resume crawls.
#SCHEDULER_PERSIST = True

# Schedule requests using a priority queue. (default)
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

# Alternative queues.
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.FifoQueue'
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.LifoQueue'

# Max idle time to prevent the spider from being closed when distributed crawling.
# This only works if queue class is SpiderQueue or SpiderStack,
# and may also block the same time when your spider start at the first time (because the queue is empty).
#SCHEDULER_IDLE_BEFORE_CLOSE = 10

# Store scraped item in redis for post-processing.
ITEM_PIPELINES = {
    'scrapy_redis.pipelines.RedisPipeline': 300
}

# The item pipeline serializes and stores the items in this redis key.
#REDIS_ITEMS_KEY = '%(spider)s:items'

# The items serializer is by default ScrapyJSONEncoder. You can use any
# importable path to a callable object.
#REDIS_ITEMS_SERIALIZER = 'json.dumps'

# Specify the host and port to use when connecting to Redis (optional).
#REDIS_HOST = 'localhost'
#REDIS_PORT = 6379

# Specify the full Redis URL for connecting (optional).
# If set, this takes precedence over the REDIS_HOST and REDIS_PORT settings.
#REDIS_URL = 'redis://user:pass@hostname:9001'

# Custom redis client parameters (i.e.: socket timeout, etc.)
#REDIS_PARAMS  = {}
# Use custom redis client class.
#REDIS_PARAMS['redis_cls'] = 'myproject.RedisClient'

# If True, it uses redis' ``SPOP`` operation. You have to use the ``SADD``
# command to add URLs to the redis queue. This could be useful if you
# want to avoid duplicates in your start urls list and the order of
# processing does not matter.
#REDIS_START_URLS_AS_SET = False

# Default start urls key for RedisSpider and RedisCrawlSpider.
#REDIS_START_URLS_KEY = '%(name)s:start_urls'

# Use other encoding than utf-8 for redis.
#REDIS_ENCODING = 'latin1'
```

我这里贴一下我`settings.py`相关代码：

```
BOT_NAME = 'jandan_redis'
SPIDER_MODULES = ['jandan_redis.spiders']
NEWSPIDER_MODULE = 'jandan_redis.spiders'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36'
ROBOTSTXT_OBEY = False
ITEM_PIPELINES = {
   'jandan_redis.pipelines.JandanRedisPipeline': 300,
}
# 以下为scrapy-redis相关设置
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379
```
其中`SCHEDULER`和` DUPEFILTER_CLASS `是必须的是，另外因为我是本机执行，默认端口，所以`REDIS_HOST`和`REDIS_PORT `不填也可以。

### 2. 改写Spiders
修改的内容有下面三个地方：

* 引入新的Spider类`RedisCrawlSpider`，替换原来的`scrapy.Spider`；

* `start_urls`去掉，改为`redis_key`，记住这个`key`，后面会用到；

* `__init__`函数修改，引入`*args`和`**kwargs`。
```
# -*- coding: utf-8 -*-
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
```

### 3. `items.py`和`pipelines.py`不变

`items.py`：

```
import scrapy

class JandanRedisItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    title_url = scrapy.Field()
 pass
```

`pipelines.py`：

```
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql

class JandanRedisPipeline(object):
    def __init__(self):
        super().__init__(

    def create_table(self):
        self.db = pymysql.connect(
            host='127.0.0.1', user='root', password='root', database='test', charset='utf8')
        sql = '''CREATE TABLE
        IF
            NOT EXISTS `jdan` (
            `id` INT ( 10 ) NOT NULL AUTO_INCREMENT,
            `title` VARCHAR ( 255 ) NOT NULL,
            `title_url` VARCHAR ( 255 ) NOT NULL,
            PRIMARY KEY ( `id` ) 
            ) ENGINE = INNODB DEFAULT CHARSET = utf8'''
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            self.db.commit()

    def drop_table(self):
        sql = '''DROP TABLE IF EXISTS `bra`'''
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            self.db.commit()

    def save_to_table(self, title, title_url):
        sql = '''INSERT INTO `jdan` (`title`, `title_url`) VALUES 
                ('%s', '%s')''' % (title, title_url)
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            self.db.commit()

    def process_item(self, item, spider):
        self.create_table()
        self.save_to_table(
            item['title'], item['title_url'])
        return item

 pass
```

### 4. 复制一份项目，重命名为xxx-slave

是的，上面的项目就是master，slave与master的不同很少，这里举最简单的例子，在`settings.py`添加：

```
REDIS_URL = 'redis://@127.0.0.1:6379'
```
`REDIS_URL `默认会将·`REDIS_HOST`和`REDIS_PORT`的设置覆盖掉，所以这两个可以不注释，不过还是建议注释掉。

### 5. 运行项目

* 输入初始url
现在我们有2个项目，一个slave，一个是master，先运行master。在master的目录下运行`scrapy crawl jandan`，运行master的spider；slave的spider先等一会。
在命令行运行的话你应该看到：
![这里写图片描述](https://img-blog.csdn.net/20180423182051442?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1NDVVRKY2Zlbmc=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)
如果你在pycharm下运行，可能看到的是这样的：
![这里写图片描述](https://img-blog.csdn.net/20180423182136226?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1NDVVRKY2Zlbmc=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)
spider已经启动了，但是没有爬起来，这是因为初始URL还没设，下面再命令行打开`redis-cli`，传入初始url，`key`就是我们在`JandanSpider`设置的`redis_key`，亦即`jandan:start_urls`。

命令行输入：

```
redis-cli.exe -p 6379
127.0.0.1:6379> lpush jandan:start_urls http://jandan.net/page/2
```

这时候程序已经跑起来了：
![这里写图片描述](https://img-blog.csdn.net/20180423183050979?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1NDVVRKY2Zlbmc=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)

最后运行slave：`scrapy crawl jandan`

* (option)暂停一下，看看RDM

`lpush jandan:start_urls http://jandan.net/page/2`，你到RDM一看：
![这里写图片描述](https://img-blog.csdn.net/20180423184249115?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1NDVVRKY2Zlbmc=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)
项目一跑起来，该值就会被取出，随后删除。
然后有新的请求加入：
![这里写图片描述](https://img-blog.csdn.net/20180423183506100?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1NDVVRKY2Zlbmc=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)

`jandan:requests`中有一行，可以看到这个是下一个要出列的`requests`，下一个是page3；

`jandan:dupefilter`也有一行，是用来存放已经爬取过的requests的指纹（page2），值为`3f1a1b57b6cab231d260d6a938b1a0f6077ebc6d`。

### 6. 改进

问题一：```slave```不运作，只有```master```运作。

原因：requests队列只有一个，master有优先权

措施：模拟添加多个`jandan:start_urls`队列

```
import redis

r = redis.Redis()
for i in range(3, 100):
    r.rpush('jandan:start_urls', 'http://jandan.net/page/%d' % i)
```
![这里写图片描述](https://github.com/SCUTJcfeng/Scrapy-redis-Projects/blob/master/jandan_redis%20-%20slave/redis_start_urls.PNG)

再次运行`master`和`slave`：
![这里写图片描述](https://github.com/SCUTJcfeng/Scrapy-redis-Projects/blob/master/jandan_redis%20-%20slave/master_slave.PNG)
呐，跑起来了。

问题二：没有实现`master`处理`items`，`slave`处理`requests`

原因：第一个项目嘛...

措施：Scrapy-redis学习系列之`二`
