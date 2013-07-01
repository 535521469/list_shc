# encoding=utf8
'''
Created on 2013-3-31
@author: Administrator
'''
from bot.dbutil import FetchSession
from bot.const import CarInfoValueConst
from crawler.shc.fe.const import FEConstant
from bot.item import CarInfo, SellerInfo
from bot.proxyutil import get_valid_proxy
from crawler.shc.fe.item import SHCFEShopInfoConstant
from crawler.tools import gen_uuid
from functools import wraps
from scrapy import log
from scrapy.http.request import Request
from scrapy.selector import HtmlXPathSelector
import datetime

def ignore_notice(parse):
    
    @wraps(parse)
    def parse_simulate(self, response):
        '''
        the page is not exist
        '''
        hxs = HtmlXPathSelector(response)
        notice_div = hxs.select('//div[@id="Notice"]')
        url = response.url
        if notice_div:
            self.log((u'ignore for not exist detail page, with Notice div '
                      '%s') % (url,), log.INFO)
        else:
            rss = parse(self, response)
            for rs in rss:
                if isinstance(rs, Request):
                    rs = rs.replace(dont_filter=True)
                yield rs
    return parse_simulate

def check_award(parse):
    '''
    see situation_pic.award.jpg
    '''
    @wraps(parse)
    def parse_simulate(self, response):
        '''
        the page is not exist
        '''
        hxs = HtmlXPathSelector(response)
        award_div = hxs.select('//div[@class="awardPic"]')
        url = response.url
        if award_div:
            
            while 1:
                proxy = get_valid_proxy.next()
                if proxy:
                    break
            try:
                precede_url = response.meta['redirect_urls'][0]
                req = response.request.copy()
                req = req.replace(url=precede_url)
                proxy_str = proxy.build_literal()
                req.meta[u'proxy'] = proxy_str
                self.log((u'check_award %s , use %s ') % (precede_url, proxy_str), log.INFO)
                yield req
                
            except Exception as e:
                self.log("error in check_award %s" % url, log.CRITICAL)
                raise e
                pass
            
        else:
            rss = parse(self, response)
            for rs in rss:
                if isinstance(rs, Request):
                    rs = rs.replace(dont_filter=True)
                yield rs
    return parse_simulate

def check_verification_code(parse):
    @wraps(parse)
    def parse_simulate(self, response):
        '''
        need you to input verification code
        '''
        hxs = HtmlXPathSelector(response)
        verification_div = hxs.select('//div[@class="w_990"]')
        url = response.url
        if url.find('support') > -1 or verification_div :
            precede_url = url[url.index(u'url=') + 4:]
            
            while 1:
                proxy = get_valid_proxy.next()
                if proxy:
                    break

            req = response.request.copy()
            rs = req.replace(url=precede_url)

            proxy_str = proxy.build_literal()
            
            req.meta[u'proxy'] = proxy_str
            msg = (u'with ver code, use proxy %s access '
                   '%s ') % (proxy_str, precede_url)
            self.log(msg, log.INFO)
            yield req
            
        else:
            rss = parse(self, response)
            for rs in rss:
                if isinstance(rs, Request):
                    rs = rs.replace(dont_filter=True)
                yield rs
                
    return parse_simulate

def check_blank_page(parse):
    @wraps(parse)
    def parse_simulate(self, response):
        '''
        the whole page is blank 
        '''
        if not len(response.body.strip()):
            url = response.url
            self.log(u'the page is blank %s' % url,
                     log.INFO)
            
            while 1:
                proxy = get_valid_proxy.next()
                if proxy:
                    break
                
            req = response.request.copy()
            proxy_str = proxy.build_literal()
            
            req.meta[u'proxy'] = proxy_str
            msg = (u'check_blank_page %s access '
                   '%s ') % (proxy_str, req.url)
            self.log(msg, log.INFO)
            yield req
            
        else:
            rss = parse(self, response)
            for rs in rss:
                if isinstance(rs, Request):
                    rs = rs.replace(dont_filter=True)
                yield rs
                
    return parse_simulate

def check_verification_code_gif(parse):
    @wraps(parse)
    def parse_simulate(self, response):
        '''
        need you to input verification code
        '''
        try:
            cookies = response.request.cookies
            hxs = HtmlXPathSelector(response)
            verification_div = hxs.select('//div[@class="w_990"]')
            url = response.url
            if verification_div:
                self.log(u'need input verification code crawl %s' % url,
                         log.CRITICAL)
                
                precede_url = url[url.index(u'url=') + 4:]
                shield_file_name = self.get_random_id()
                
                self.log((u'use ip proxy to request %s again , '
                          'shield %s') % (precede_url, shield_file_name),
                         log.INFO)
                proxy = self.get_next_proxy(cookies)
                
                if self.is_develop_debug(cookies):
                    self.save_body(self.build_shield_file_dir(cookies),
                                    shield_file_name + u'.html', response)
                
                yield Request(precede_url, self.parse, meta={'proxy':proxy},
                              cookies=cookies, dont_filter=True)
                    
        except Exception:
            rss = parse(self, response)
            if rss:
                for rs in rss:
                    if isinstance(rs, Request):
                        rs = rs.replace(dont_filter=True)
                    yield rs
                
    return parse_simulate

def with_ip_proxy(parse):
    @wraps(parse)
    def parse_simulate(self, response):
        
        rss = parse(self, response)
        if rss:
            for rs in rss:
                if isinstance(rs, Request) :
                    proxy = get_valid_proxy.next()
                    if proxy:
                        proxy_str = proxy.build_literal()
                        rs = rs.replace(dont_filter=True)
                        rs.meta['proxy'] = proxy_str
                        msg = (u'with_ip_proxy use proxy %s access '
                               '%s ') % (proxy_str, rs.url)
                        self.log(msg, log.INFO)
                yield rs
        
    return parse_simulate

def list_page_parse_4_remove_duplicate_detail_page_request(parse):
    
    @wraps(parse)
    def parse_simulate(self, response):
        rss = parse(self, response)
        from crawler.shc.fe.spiders import CarDetailSpider, CarListSpider
        if rss:
            rs_len = 0
            for rs in rss:
                if isinstance(rs, Request):
                    # detail spider
                    if rs.callback.im_class == CarDetailSpider:
                        rs_len = rs_len + 1
                        custom_flag = rs.cookies.get(FEConstant.CUSTOMER_FLAG, CarInfoValueConst.car_source_unkonwn)
                        fs = FetchSession()
                        try:
                            declaredate = rs.cookies.get(SHCFEShopInfoConstant.declaretime, None)
                            ci = CarInfo()
                            ci.carsourcetype = custom_flag
                            if rs.url.find(u'jump.zhineng') <> -1:
                                ci.popularizeurl = rs.url
                            else:
                                ci.sourceurl = rs.url
                            
                            if declaredate:
                                query_clause = fs.query(CarInfo)
                                if ci.sourceurl:
                                    query_clause = query_clause.filter(
                                               CarInfo.sourceurl == ci.sourceurl)
                                elif ci.popularizeurl:
                                    query_clause = query_clause.filter(
                                               CarInfo.popularizeurl == ci.popularizeurl)

                                exist_ci = query_clause.filter(CarInfo.declaredate == declaredate).first()
                                if exist_ci:
                                    self.log((u'ignore dup %s detail '
                                              'page %s') % (exist_ci.declaredate, rs.url,), log.INFO)
                                    continue
                                else:
                                    exist_ci = query_clause.filter(CarInfo.statustype == None).first()
                                    if exist_ci:
                                        self.log((u'ignore dup detail '
                                                  'page %s') % (rs.url,), log.INFO)
                                        continue

                                ci.declaredate = declaredate


                            #===================================================
                            # add sourcetype and persist to db
                            #===================================================
                            ci.sourcetype = '58'
                            
                            fs.add(ci)
                            self.log(u'add detail page %s %s %s' % (ci.declaredate, rs.url, custom_flag),
                                     log.INFO)
                                
                                #===============================================
                                # not crawl the detail page this service 
                                #===============================================
#                                yield rs
                        except Exception as e:
                            fs.rollback()
                            self.log(u'something wrong %s' % str(e), log.CRITICAL)
                            raise e
                        else:
                            fs.commit()
                        finally:
                            fs.close()
                    elif rs.callback.im_class == CarListSpider:
                        yield rs
                    
    return parse_simulate

def detail_page_parse_4_save_2_db(parse):
    
    def stuff_ci(ci, sellerinfo, current_city):
        contacter_url = sellerinfo.get(SHCFEShopInfoConstant.contacter_url)
        ci.statustype = u'2' if contacter_url is None else '1' 
        ci.title = sellerinfo.get(SHCFEShopInfoConstant.title)
        ci.declaredate = sellerinfo.get(SHCFEShopInfoConstant.declaretime)
        ci.fetchdatetime = datetime.datetime.now()
        ci.lastactivedatetime = datetime.datetime.now()
        ci.price = sellerinfo.get(SHCFEShopInfoConstant.price)
        ci.cartype = sellerinfo.get(SHCFEShopInfoConstant.cartype)
        ci.contacter = sellerinfo.get(SHCFEShopInfoConstant.contacter)
        ci.contacterurl = contacter_url
        ci.contacterphonepicname = sellerinfo.get(SHCFEShopInfoConstant.contacter_phone_picture_name)
        ci.carcolor = sellerinfo.get(SHCFEShopInfoConstant.car_color)
        ci.roadhaul = sellerinfo.get(SHCFEShopInfoConstant.road_haul)
        ci.displacement = sellerinfo.get(SHCFEShopInfoConstant.displacement)
        ci.gearbox = sellerinfo.get(SHCFEShopInfoConstant.gearbox)
        ci.licenseddate = sellerinfo.get(SHCFEShopInfoConstant.license_date)
        ci.sourceurl = sellerinfo.get(SHCFEShopInfoConstant.info_url)
        ci.cityname = current_city
        carsourcetype = sellerinfo.get(SHCFEShopInfoConstant.custom_flag)
        ci.carsourcetype = carsourcetype
        ci.contacterphonepicurl = sellerinfo.get(SHCFEShopInfoConstant.contacter_phone_url)
        ci.sourcetype = u'58'
        
    @wraps(parse)
    def parse_simulate(self, response):
        rss = parse(self, response)
        from crawler.shc.fe.spiders import PersonPhoneSpider, CustomerShopSpider
        if rss:
            for rs in rss:
                fs = FetchSession()
                try:
                    if not isinstance(rs, Request):

                        contacter_url = rs.get(SHCFEShopInfoConstant.contacter_url)
                        si = fs.query(SellerInfo).filter(SellerInfo.sellerurl == contacter_url).first()
                        sourceurl = rs.get(SHCFEShopInfoConstant.info_url)
                        
                        if si is not None:
                            
                            ci = fs.query(CarInfo).filter(CarInfo.sourceurl == sourceurl).first()
                            if ci is not None:
                                #===================================================
                                # already exists
                                #===================================================
                                self.log(u'parse detail page,detail url already exists ', log.CRITICAL)
                            else:
                                ci = CarInfo()
                                stuff_ci(ci, rs, rs.get(SHCFEShopInfoConstant.cityname))
                                try:
                                    popularizeurl = response.meta['redirect_urls'][0]
                                    if popularizeurl.find(u'jump.zhineng') <> -1:
                                        ci.popularizeurl = popularizeurl
                                except Exception as e:
                                    pass
                                
                                ci.sellerid = si.seqid
                                fs.add(ci)
                                
                            self.log(u"give up to crawl exist seller info "
                                     "%s %s %s" % (ci.cityname, contacter_url, si.seqid),
                                     log.INFO)
                        else:
                            ci = fs.query(CarInfo).filter(CarInfo.sourceurl == sourceurl).first()
                            if ci is not None:
                                self.log(u'parse detail page,detail url already exists ', log.CRITICAL)
                            else:
                                ci = CarInfo()
                                ci.sellerid = gen_uuid()
                                stuff_ci(ci, rs, rs.get(SHCFEShopInfoConstant.cityname))
                                fs.add(ci)
                            
                            si = SellerInfo()
                            si.seqid = ci.sellerid
                            si.selleraddress = rs.get(SHCFEShopInfoConstant.shop_address)
                            si.sellername = rs.get(SHCFEShopInfoConstant.shop_name)
                            si.sellerphone = rs.get(SHCFEShopInfoConstant.shop_phone)
                            si.sellerurl = contacter_url
                            
                            si.enterdate = rs.get(SHCFEShopInfoConstant.enter_time)
                            fs.add(si)
                        
                            if contacter_url is not None:
                                yield Request(contacter_url,
                                              CustomerShopSpider().parse,
                                              dont_filter=True,
                                              cookies={
                                                       SHCFEShopInfoConstant.contacter_url:ci.contacterurl,
                                                       SHCFEShopInfoConstant.carid:ci.seqid,
                                                       SHCFEShopInfoConstant.sellerid:si.seqid,
                                                       },
                                              )
                        
                        phone_url = rs.get(SHCFEShopInfoConstant.contacter_phone_url)
                        if phone_url is not None:
                            yield Request(phone_url, PersonPhoneSpider().parse,
                                          cookies={
                                                   SHCFEShopInfoConstant.contacter_phone_picture_name:ci.contacterphonepicname,
                                                   SHCFEShopInfoConstant.carid:ci.seqid,
                                                   }, dont_filter=True)
                except Exception as e:
                    self.log(u'something wrong %s' % str(e), log.CRITICAL)
                    fs.rollback()
                else:
                    fs.commit()
                finally:
                    fs.close()
    return parse_simulate

def seller_page_parse_4_save_2_db(parse):
    
    def stuff_si(si, rs):
        si.selleraddress = rs.get(SHCFEShopInfoConstant.shop_address)
        si.sellername = rs.get(SHCFEShopInfoConstant.shop_name)
        si.sellerphone = rs.get(SHCFEShopInfoConstant.shop_phone)
        si.enterdate = rs.get(SHCFEShopInfoConstant.enter_time)
        
    @wraps(parse)
    def parse_simulate(self, response):
        rss = parse(self, response)
        if rss:
            for rs in rss:
                fs = FetchSession()
                try:
                    if not isinstance(rs, Request):
                        si = fs.query(SellerInfo).filter(SellerInfo.seqid == rs.get(SHCFEShopInfoConstant.sellerid)).first()
                        if si is not None:
                            stuff_si(si, rs)
                except Exception as e:
                    self.log(u'something wrong %s' % str(e), log.CRITICAL)
                else:
                    fs.commit()
                finally:
                    fs.close()
    return parse_simulate

