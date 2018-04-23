# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy_redis.pipelines import RedisPipeline
import redis
import pymysql

class JandanRedisPipeline(object):
    def __init__(self):
        super().__init__()
        # self.r = redis.Redis()

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
