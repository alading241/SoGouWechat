# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SogouItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    _id = scrapy.Field()    # 数据存入 mangodb 时所必须的字段
    keyword = scrapy.Field()    # 搜索关键字
    public_name = scrapy.Field()    # 微信公众号名称
    open_id = scrapy.Field()    # 微信公众号唯一开放id
    profile_url = scrapy.Field()    # 微信公众号的简介链接
    headimage = scrapy.Field()  # 微信公众号头像
    public_id = scrapy.Field()  # 微信公众号id
    qrcode = scrapy.Field()     # 微信公众号二维码链接
    introduction = scrapy.Field()   # 微信公众号功能介绍
    authentication = scrapy.Field()     # 微信公众号认证主体
    post_perm = scrapy.Field()  # 月平均提交量
    view_perm = scrapy.Field()  # 历史文章总量
