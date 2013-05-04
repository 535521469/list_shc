BOT_NAME = 'SHCSpider'
SPIDER_MODULES = ['crawler.shc.fe.spiders', ]
LOG_ENCODING = u'UTF-8'

RETRY_TIMES = 500
DOWNLOADER_MIDDLEWARES = {'crawler.shc.fe.middlewares.ProxyRetryMiddleWare':450,
                          'scrapy.contrib.downloadermiddleware.retry.RetryMiddleware':None
                           }

DOWNLOAD_TIMEOUT=1.5
DOWNLOAD_DELAY=0.8

USER_AGENT='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'