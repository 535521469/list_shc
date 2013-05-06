# encoding=UTF-8
'''
Created on 2013-5-1
@author: Administrator
'''
from bot.config import configdata
from const import ScrapyConst, ListSpiderConst
from crawler.shc.fe.const import FEConstant as const
from scrapy.cmdline import execute
from scrapy.settings import CrawlerSettings
import os

class SpiderProcess(object):
    
    def __init__(self, city_name, configdata):
        self.city_name = city_name
        self.configdata = dict(configdata)
        self.configdata[const.CURRENT_CITY] = city_name
    
    def run(self):
        feconfig = self.configdata[const.FE_CONFIG]
        try:
        #=======================================================================
        # if the city use the default config
        #=======================================================================
            city_config = eval(feconfig[self.city_name])
        except Exception:
            city_config = {}
        
        start_page = city_config.get(const.START_PAGE,
                             feconfig[const.DEFAULT_START_PAGE])
        end_page = city_config.get(const.END_PAGE,
                                   feconfig[const.DEFAULT_END_PAGE])
#        values = {
#                  const.CONFIG_DATA:self.configdata,
#                  const.START_PAGE:int(start_page),
#                  const.END_PAGE:int(end_page),
#                  }
#        settings = u'crawler.shc.fe.settings'
#        module_import = __import__(settings, {}, {}, [''])
#        settings = CrawlerSettings(module_import, values=values)
#        execute(argv=["scrapy", "crawl", 'SHCSpider' ], settings=settings)

        values = configdata.get(ListSpiderConst.ListSettings, {})
        
        values.update(**{
                  const.CONFIG_DATA:self.configdata,
                  const.START_PAGE:int(start_page),
                  const.END_PAGE:int(end_page),
                  })
        
        if ScrapyConst.Console in values:
            if values[ScrapyConst.Console] == u'1':# out to console
                values[ScrapyConst.LOG_FILE] = None
            else:
                log_dir = values.get(ScrapyConst.LOG_DIR, os.getcwd())
                if ScrapyConst.LOG_FILE in values:
                    log_file = values[ScrapyConst.LOG_FILE]
                    values[ScrapyConst.LOG_FILE] = os.sep.join([log_dir , log_file])
                    
        settings_path = u'crawler.shc.fe.settings'
        module_import = __import__(settings_path, {}, {}, [''])
        settings = CrawlerSettings(module_import, values=values)
        execute(argv=["scrapy", "crawl", 'SHCSpider' ], settings=settings)
        
if __name__ == '__main__':
    sp = SpiderProcess(u'广州', configdata).run()
        
