"""
这是一个工具脚本,用来处理从 scrapy 的 response 中获取的 Set_Cookies
实现的功能是将 [ bytes, bytes] 类型的数据转换成 标准的 cookie 字典形式
形如: ['ABTEST=0|1558615060|v1', ' expires=Sat, 22-Jun-19 12:37:40 GMT', ' path=/']
转换结果: {'ABTEST': '0|1558615060|v1', 'expires': 'Thu,01-Dec-199416:00:00GMT', 'path': '/'}
"""


def process_cookie(cookie):
    """
    将 bytes 类型的数据转换成 dict
    :param cookie:
    :return:
    """
    # 创建字典 存储最终的结果
    cookies = dict()
    # 遍历cookie [bytes, bytes]
    for c in cookie:
        # 将 bytes 类型转换成 str
        c = str(c, encoding='utf-8')
        # 将 str 首先按照 ";" 拆分
        items = c.split(';')
        for item in items:
            # 再按照 "=" 拆分
            key = item.split('=')[0].replace(' ', '')
            value = item.split('=')[1].replace(' ', '')
            cookies[key] = value
    return cookies
