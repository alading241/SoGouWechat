"""
这是基于搜狗的微信公众号爬虫
获取的微信公众号链接是有其有效期的(貌似是6个小时)
搜狗的反爬策略如下:
1.搜索结果为微信临时链接，浏览有效期为6个小时

2.搜索结果限制浏览页数为10页，登录后最多可以浏览100页内容

3.1分钟内连续翻页达到30次以上将出现验证码

4.文章页面过于频繁访问将被封禁2~24小时，所有微信文章将显示请使用微信扫码阅读

5.经常触发验证码的IP将被拉黑，所有搜索均需要先输入验证码
"""
import os
import re
from urllib.parse import urljoin
import requests
import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.signals import spider_closed
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy_redis.spiders import RedisSpider
from twisted.internet.error import TCPTimedOutError, DNSLookupError
from SoGou.items import SogouItem
from SoGou.tools.process_scrapy_cookies import process_cookie


get_post_view_perm = re.compile('<script>var account_anti_url = "(.*?)";</script>')


class WechatPublicSpider(RedisSpider):
    # 爬虫名字
    name = "wechatPublic"
    # 爬虫启动命令
    redis_key = "WechatPublicSpider:items"

    def __init__(self, settings):
        super(WechatPublicSpider, self).__init__()
        self.keyword_file_list = os.listdir(settings.get("KEYWORD_PATH"))
        # 请求的URL type 代表搜索的类型  1 ----> 微信公众号    2 ----> 文章  page 代表页号   默认是 1
        self.search_url = "https://weixin.sogou.com/weixin?query={keyword}" \
                          "&_sug_type_=&s_from=input&_sug_=n&type=1&page={page}&ie=utf8"
        # 请求链接  在此处因为大意 丢掉了 weixin 结果一直响应 400 切记认真分析!!!!
        self.base_url = "https://weixin.sogou.com/weixin"
        # 请求头
        self.headers = {
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate, br',
            # 'Accept-Language': 'zh-CN,zh;q=0.9',
            # 'Connection': 'keep-alive',
            'Host': 'weixin.sogou.com',
            # 'Pragma': 'no-cache',
            # 'Referer': 'https://weixin.sogou.com/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
        }
        # 全局的默认参数
        self.default_value = "暂无信息"

    @staticmethod
    def __get_post_view_perm(text):
        """
        从 requests 或者 scrapy 获取响应的 text 中匹配 account_anti_url
        :param text: requests 或者 scrapy 获取响应的 text
        :return:
        """
        result = get_post_view_perm.findall(text)
        if not result or len(result) < 1 or not result[0]:
            return None

        r = requests.get('http://weixin.sogou.com{}'.format(result[0]))
        if not r.ok:
            return None

        if r.json().get('code') != 'success':
            return None

        return r.json().get('msg')

    def parse_err(self, failure):
        """
        异常处理回调函数,请求失败的 Request 对象 将在从按照 自定义的方式进行处理:
        1.可以选择将失败的 Request 对象重新加入请求队列 重新请求
        2.也可以自定义方法将失败的 Request 对象 记录到文件中,等全部抓取完毕再重新抓取
        :param failure:
        :return:
        """
        if failure.check(TimeoutError, TCPTimedOutError, DNSLookupError):
            # 失败的请求
            request = failure.request
            # 将失败的请求重新加入请求队列
            self.server.rpush(self.redis_key, request)

        if failure.check(HttpError):
            # 获取响应
            response = failure.value.response
            # 重新加入请求队列
            self.server.rpush(self.redis_key, response.url)
        return

    def start_requests(self):
        """
        循环读取文件列表,生成初始请求
        :return:
        """
        # 判断关键字文件是否存在
        if not self.keyword_file_list:
            # 抛出异常并关闭爬虫
            raise CloseSpider("需要关键字文件")
        for keyword_file in self.keyword_file_list:
            # 循环获取关键字文件路径
            file_path = os.path.join(self.settings.get("KEYWORD_PATH"), keyword_file)
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                for keyword in f.readlines():
                    # 消除关键字末尾的空白字符
                    keyword = keyword.strip()
                    print("查看获取的关键字:", keyword)
                    # 发起请求
                    yield scrapy.Request(url=self.search_url.format(keyword=keyword, page=str(1)),
                                         callback=self.parse, errback=self.parse_err,
                                         headers=self.headers,
                                         meta={'keyword': keyword, 'dont_redirect': True,
                                               'handle_httpstatus_list': [302]}
                                         )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 配置信息
        settings = crawler.settings
        # 爬虫信息
        spider = super(WechatPublicSpider, cls).from_crawler(crawler, settings, *args, **kwargs)
        # 中止爬虫信号
        crawler.signals.connect(spider.spider_closed, signal=spider_closed)
        # 返回spider 不然会无法运行 start_requests 方法
        return spider

    def spider_closed(self, spider):
        """
        自定义的爬虫关闭时执行的操作
        :param spider:
        :return:
        """
        # 输出日志,提示关闭爬虫
        self.logger.info(' Spider closed : %s ', spider.name)
        # 是具体的情况添加如下两个文件的操作方法
        # spider.record_file.write("]")
        # spider.record_file.close()

    def parse(self, response):
        """
        列表页的解析函数
        :param response:
        :return:
        """
        if response.status == 200:
            print("查看响应:", response.text)
            # 获取 平均月发量 和 历史文章总量
            post_view_perms = WechatPublicSpider.__get_post_view_perm(response.text)
            # 获取搜索结果的li
            results = response.xpath('//div[@class="news-box"]/ul/li')
            # 搜索关键字
            keyword = response.meta['keyword']
            # 是否有下一页
            is_next = response.xpath('//a[@id="sogou_next"]/@href').extract_first()
            # 有无搜索结果
            if len(results) != 0:
                for result in results:
                    # 创建 item
                    item = SogouItem()
                    # 获取公众号名称
                    public_name = result.xpath('./div/div[@class="txt-box"]/p[@class="tit"]/'
                                               'a/descendant-or-self::text()').extract()
                    # 公众号唯一的 open_id
                    open_id = result.xpath('./@d').extract_first()
                    # 公众号的详情页链接,需要跟 base_url 进行拼接
                    profile_url = result.xpath('./div/div/a/@href').extract_first()
                    # 公众号头像,需要与 https: 进行拼接
                    headimage = result.xpath('./div/div[@class="img-box"]/a/img/@src').extract_first()
                    # 微信公众号id
                    public_id = result.xpath('./div/div[@class="txt-box"]/p[@class="info"]/'
                                             'child::node()/text()').extract_first()
                    # 微信公众号二维码链接
                    qrcode = result.xpath('./div/div[@class="ew-pop"]/span/img[1]/@src').extract_first()
                    # 微信公众号简介,需要 做序列拼接
                    introduction = result.xpath('./dl[1]/dd/descendant-or-self::text()').extract()
                    print("查看获取的:", introduction)
                    # 微信认证主体
                    authentication = result.xpath('./dl/dd/i[@class="identify"]/../text()').extract()
                    item['keyword'] = keyword
                    item['public_name'] = "".join([i.strip() for i in public_name if i])
                    item['open_id'] = open_id if open_id else self.default_value
                    item['profile_url'] = urljoin(self.base_url, profile_url) if profile_url else self.default_value
                    item['headimage'] = "https:" + headimage if headimage else self.default_value
                    item['public_id'] = public_id if public_id else self.default_value
                    item['qrcode'] = qrcode if qrcode else self.default_value
                    item['introduction'] = " ".join([i.strip() for i in introduction if i])
                    item['authentication'] = " ".join([i.strip() for i in authentication if i])
                    if post_view_perms:
                        if open_id in post_view_perms:
                            post_view_perm = post_view_perms[open_id].split(',')
                            if len(post_view_perm) == 2:
                                item['post_perm'] = int(post_view_perm[0])
                                item['view_perm'] = int(post_view_perm[1])
                        else:
                            item['post_perm'] = -1
                            item['view_perm'] = -1
                    yield item
                # 判断是否有下一页
                if is_next:
                    next_url = urljoin(self.base_url, is_next)
                    # print(response.headers.getlist('Set-Cookie'))
                    # 响应cookie
                    cookies = response.headers.getlist('Set-Cookie')
                    # str 转换 dict
                    cookies = process_cookie(cookies)
                    print(cookies)
                    # 发起下一页的请求
                    yield scrapy.Request(url=next_url, callback=self.parse, errback=self.parse_err,
                                         headers=self.headers, cookies=cookies,
                                         meta={'keyword': keyword,
                                               'dont_redirect': True, 'handle_httpstatus_list': [302]})

