"""
自定义的代理中间件
"""
import random
import time

import requests


class RandomProxy(object):

    def __init__(self):
        self.proxies_list = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def save_proxies(self):
        """

        :return:
        """
        while True:
            # 获取代理
            response = requests.get("http://39.107.59.59/get?spider_name=guomei")
            # json ---> dict
            data = response.json()
            # 响应码
            code = data.get('ERRORCODE')
            # 代理
            result = data.get('RESULT')
            if code == "0" and result:
                return self.proxies_list.extend(result)
            time.sleep(3)

    def get_random_proxies(self):
        """
        获取随机的代理
        :return:
        """
        if not self.proxies_list:
            self.save_proxies()
        return random.choice(self.proxies_list)

    def del_proxies(self, proxy_value):
        """
        删除代理
        :param proxy_value:
        :return:
        """
        try:
            self.proxies_list.remove(proxy_value)
        except Exception as e:
            print(e)
            pass

    def process_request(self, request, spider):
        """

        :param request:
        :param spider:
        :return:
        """
        # 随机代理
        proxy = self.get_random_proxies()
        request.meta['proxy'] = "http://{ip}:{port}".format(**proxy)
        request.meta['proxy_value'] = proxy

    def process_response(self, request, response, spider):
        """

        :param request:
        :param response:
        :param spider:
        :return:
        """
        if response.status != 200:
            # 失效代理
            proxy_value = request.meta['proxy_value']
            # 删除失效代理
            self.del_proxies(proxy_value)
            # 失败请求重新加入请求队列
            return request.replace(url=request.url, dont_filter=True)
        return response

    def process_exception(self, request, exception, spider):
        """

        :param request:
        :param exception:
        :param spider:
        :return:
        """
        # 失效的代理
        proxy_value = request.meta['proxy_value']
        # 删除失效的代理
        self.del_proxies(proxy_value)
        # 失败请求重新加入请求队列
        return request.replace(url=request.url, dont_filter=True)
