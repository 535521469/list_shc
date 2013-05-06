# encoding=utf8
'''
Created on 2013-3-20
@author: corleone
'''
from crawler.shc.fe.const import FEConstant as const
from multiprocessing import Process
from sched import scheduler
from scrapy.cmdline import execute
from scrapy.settings import CrawlerSettings
import collections
import datetime
import time
from bot.config import configdata
from const import ListSpiderConst, ScrapyConst, AppConst
import os

class SpiderProcess(Process):
    
    def __init__(self, city_name, configdata):
        Process.__init__(self)
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

spider_process_mapping = {}

def add_task(root_scheduler):
    
    city_names = configdata[const.FE_CONFIG][const.FE_CONFIG_CITIES].split(u',')
    processes = collections.deque()
    
    for city_name in city_names :
        p = SpiderProcess(city_name, configdata)
        spider_process_mapping[city_name] = p
        processes.append(p)
        
    if len(processes):
        root_scheduler.enter(1, 1, check_add_process,
                             (spider_process_mapping, processes,
                              root_scheduler, configdata))
            
def check_add_process(spider_process_mapping, processes,
                      root_scheduler, configdata):
    
    alives = filter(Process.is_alive, spider_process_mapping.values())
    
    if len(processes):
        pool_size = int(configdata[const.FE_CONFIG].get(const.MULTI, 1))
        if len(alives) < pool_size:
            p = processes.popleft()
            print (u'%s enqueue %s ,pool size %d , %d cities '
                   'waiting ') % (datetime.datetime.now(), p.city_name,
                                  pool_size, len(processes))
            root_scheduler.enter(0, 1, p.start, ())
        #=======================================================================
        # check to add process 10 seconds later
        #=======================================================================
            if not len(processes):
                print (u'%s all process enqueue ...' % datetime.datetime.now())
                
        root_scheduler.enter(5, 1, check_add_process
                             , (spider_process_mapping, processes,
                                root_scheduler, configdata))
    else:
        if len(alives) == 0:
            print ('%s crawl finished ... ' % datetime.datetime.now())
        else :
            root_scheduler.enter(5, 1, check_add_process
                                 , (spider_process_mapping, processes,
                                    root_scheduler, configdata))

if __name__ == '__main__':
    
    frequence = configdata[AppConst.app_config].get(AppConst.app_config_frequence, 1800)
    frequence = int(frequence)
    while 1:
        root_scheduler = scheduler(time.time, time.sleep)
        root_scheduler.enter(0, 0, add_task, (root_scheduler,))
        root_scheduler.run()
        print u'%s sleep %s seconds' % (datetime.datetime.now(), frequence)
        time.sleep(frequence)
