# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from SoGou.utils import get_db
mongo_db = get_db()


class SogouPipeline(object):
    def process_item(self, item, spider):
        return item


# 以下代码是存储到 mongodb时需要的代码
class ResultMongoPipeline(object):
    """抓取结果导入 mongo"""

    def __init__(self, settings):
        self.collections_name = settings.get('RESULT_COLLECTIONS_NAME')

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(settings)

    def process_item(self, item, spider):
        mongo_db[self.collections_name].insert(item)
        return item
