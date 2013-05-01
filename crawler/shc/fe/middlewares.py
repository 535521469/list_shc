# encoding=utf8
'''
Created on 2013-4-15
@author: corleone
'''
from bot.proxyutil import get_valid_proxy
from scrapy import log
from scrapy.contrib.downloadermiddleware.retry import RetryMiddleware

class ProxyRetryMiddleWare(RetryMiddleware):

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0)
        if retries <= self.max_retry_times - 1:
            next_proxy = get_valid_proxy.next()
            rs = request.copy()
            if next_proxy:
                proxy_str = next_proxy.build_literal()
                rs = rs.replace(dont_filter=True)
                rs.meta['proxy'] = proxy_str
                msg = (u'use to %s access %s ') % (proxy_str, rs.url)
                rs.meta[u'proxy'] = proxy_str 
                spider.log(msg, log.DEBUG)
            else:
                try:
                    del rs.meta[u'proxy']
                    msg = (u'use self ip asscess %s') % (rs.url)
                    spider.log(msg, log.DEBUG)
                except :pass
            
        return RetryMiddleware._retry(self, rs, reason, spider)
