#!/usr/bin/env python
# encoding: utf-8

import scrapy
import json
import datetime
import urlparse
from lxml import etree
import requests

from datetime import datetime as dte
from BusCrawl.item import LineItem
from base import SpiderBase

from BusCrawl.utils.tool import get_pinyin_first_litter
from BusCrawl.utils.tool import get_redis
from scrapy.conf import settings
from pymongo import MongoClient


class BjkySpider(SpiderBase):
    name = "bjky"
    custom_settings = {
        "ITEM_PIPELINES": {
            'BusCrawl.pipeline.MongoPipeline': 300,
        },

        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'BusCrawl.middleware.BrowserRandomUserAgentMiddleware': 400,
            'BusCrawl.middleware.ProxyMiddleware': 410,
#             'BusCrawl.middleware.BjkyHeaderMiddleware': 410,
        },
#        "DOWNLOAD_DELAY": 0.1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
    }

    def query_cookies(self):
#         db_config = settings.get("MONGODB_CONFIG")
#         client = MongoClient(db_config["url"])
#         db = client[db_config["db"]]
        result = self.db.bjkyweb_rebot.find({"is_active": True}).sort([("last_login_time", -1)]).limit(5)
        url = "http://www.e2go.com.cn/TicketOrder/SearchSchedule"
        cookies = {}
        for i in result:
            response = requests.get(url, cookies=json.loads(i['cookies']))
            result = urlparse.urlparse(response.url)
            if result.path != '/Home/Login':
                cookies = json.loads(i['cookies'])
                break
        return cookies

    def is_end_city(self, start, end):
        if not hasattr(self, "_sta_dest_list"):
            self._sta_dest_list = {}
        s_sta_name = start['name']
        if s_sta_name != u'首都机场站':
            if s_sta_name == u'丽泽桥':
                s_sta_name = u'丽泽客运站'
            else:
                s_sta_name = s_sta_name+'客运站'

        if s_sta_name not in self._sta_dest_list:
            self._sta_dest_list[s_sta_name] = self.db.line.distinct('d_city_name', {'crawl_source': 'ctrip', 's_sta_name':s_sta_name})

        result = self._sta_dest_list[s_sta_name]
        if end['StopName'] not in result:
            return 0
        else:
            return 1

    def query_all_end_station(self):
        r = get_redis()
        key = "bjky_end_station"
        end_station_list = r.get(key)
        if end_station_list:
            return end_station_list
        else:
            end_station_list = []
            letter = 'abcdefghijklmnopqrstuvwxyz'
            for i in letter:
                for j in letter:
                    query = i+j
                    end_station_url = 'http://www.e2go.com.cn/Home/GetBusStops?q=%s'%query
                    res_lists = requests.get(end_station_url)
                    res_lists = res_lists.json()
                    for res_list in res_lists:
                        end_station_list.append(json.dumps(res_list))
            r.set(key, json.dumps(list(set(end_station_list))))
            r.expire(key, 2*24*60*60)
            end_station_list = r.get(key)
            if end_station_list:
                return end_station_list
        return end_station_list

    def start_requests(self):
#         cookies = {"ASP.NET_SessionId": "vv3tb0fucnaxkmoudsxs5swa"}
        db_config = settings.get("MONGODB_CONFIG")
        client = MongoClient(db_config["url"])
        self.db = client[db_config["db"]]
        cookies = self.query_cookies()
        if cookies:
            start_url = "http://www.e2go.com.cn/TicketOrder/SearchSchedule"
    #         cookie ="Hm_lvt_0b26ef32b58e6ad386a355fa169e6f06=1456970104,1457072900,1457316719,1457403102; ASP.NET_SessionId=uuppwd3q4j3qo5vwcka2v04y; Hm_lpvt_0b26ef32b58e6ad386a355fa169e6f06=1457415243"
    #         headers={"cookie":cookie}
            yield scrapy.Request(start_url,
                                 method="GET",
                                 cookies=cookies,
                                 callback=self.parse_url,
                                 meta={'cookies': cookies})
        else:
            self.logger.error("cookies is {}", )

    def parse_url(self, response):
        cookies = response.meta["cookies"]
        result = urlparse.urlparse(response.url)
        if result.path == '/Home/Login':
            self.logger.error("parse_url: cookie is expire", )
            return
        start_station_list = [
            {'name': u"六里桥",'code': "1000"},
            {'name': u"首都机场站",'code':"1112"},
            {'name': u"赵公口",'code':"1103"},
            {'name': u"木樨园",'code': "1104"},
            {'name': u"丽泽桥",'code': "1106"},
            {'name': u"新发地",'code': "1107"},
            {'name': u"莲花池",'code': "1108"},
            {'name': u"四惠",'code': "1109"},
            {'name': u"永定门",'code': "1110"},
            {'name': u"北郊",'code': "1111"},
            ]

        queryline_url = "http://www.e2go.com.cn/TicketOrder/SearchSchedule"
#         end_station_list = self.query_all_end_station()
#         end_station_list = json.loads(end_station_list)
#         print "end_station_list",len(end_station_list)
#         print 'end_station_list',type(end_station_list)
#         print end_station_list
        for start in start_station_list:
            dest_list = []
            dest_list = self.get_dest_list("北京", '北京', start["name"])
            for s in dest_list:
                name, code = s["name"], s["code"]
                end = {"StopName": name, "city_code": code, "StopId": s['dest_id']}
#             for end in end_station_list:
#                     end = json.loads(end)
#                     if self.is_end_city(start, end):
                today = datetime.date.today()
                for i in range(2, 9):
                    sdate = str(today+datetime.timedelta(days=i))
                    if self.has_done(start["name"], end["StopName"], sdate):
                        self.logger.info("ignore %s ==> %s %s" % (start["name"], end["StopName"], sdate))
                        continue
                    data = {
                        "ArrivingStop": unicode(end['StopName']),
                        "ArrivingStopId": unicode(end['StopId']),
                        "ArrivingStopJson": json.dumps(end),
                        "DepartureDate": sdate,
                        "Order": "DepartureTimeASC",
                        "RideStation": start["name"],
                        "RideStationId": start["code"]
                    }
                    yield scrapy.FormRequest(queryline_url, formdata=data,
                                             callback=self.parse_line,
                                             cookies=cookies,
                                             meta={"start": start,"end": end, "date": sdate})

    def parse_line(self, response):
        "解析班车"
        start = response.meta["start"]
        end = response.meta["end"]
        sdate = response.meta["date"]
        content = response.body
        self.mark_done(start["name"], end["StopName"], sdate)
        if not isinstance(content, unicode):
            content = content.decode('utf-8')
        sel = etree.HTML(content)
        scheduleList = sel.xpath('//div[@id="scheduleList"]/table/tbody/tr')
        for i in range(0, len(scheduleList), 2):
            s = scheduleList[i]
            time = s.xpath('td[@class="departureTimeCell"]/span/text()')[0]
            station = s.xpath('td[@class="routeNameCell"]/span/text()')
            scheduleIdSpan = s.xpath('td[@class="scheduleAndBusLicenseCes"]/span[@class="scheduleSpan"]/span[@class="scheduleIdSpan"]/text()')[0]
            scheduleIdSpan = scheduleIdSpan.replace('\r\n', '').replace('\t',  '').replace(' ',  '')
            price = s.xpath('td[@class="ticketPriceCell"]/span[@class="ticketPriceSpan"]/span[@class="ticketPriceValueSpan"]/text()')[0]
            ScheduleString = s.xpath('td[@class="operationCell"]/@data-schedule')[0]
            left_tickets = 45
            left_less = s.xpath('td[@class="memoCell"]/span/@class')
            if left_less:
                left_tickets = 0

            station_code_mapping = {
                u"六里桥": "1000",
                u"首都机场站": "1112",
                u"赵公口": "1103",
                u"木樨园": "1104",
                u"丽泽桥": "1106",
                u"新发地": "1107",
                u"莲花池": "1108",
                u"四惠": "1109",
                u"永定门": "1110",
                u"北郊": "1111",
                }
            attrs = dict(
                s_province = '北京',
                s_city_name = "北京",
                s_city_id = '',
                s_city_code= get_pinyin_first_litter(u"北京"),
                s_sta_name = station[0],
                s_sta_id = station_code_mapping[station[0]],
                d_city_name = end['StopName'],
                d_city_code= get_pinyin_first_litter(end['StopName']),
                d_city_id = end['StopId'],
                d_sta_name = end['StopName'],
                d_sta_id = '',
                drv_date = sdate,
                drv_time = time,
                drv_datetime = dte.strptime("%s %s" % (sdate, time), "%Y-%m-%d %H:%M"),
                distance = "0",
                vehicle_type = "",
                seat_type = "",
                bus_num = scheduleIdSpan,
                full_price = float(price),
                half_price = float(price)/2,
                fee = 0,
                crawl_datetime = dte.now(),
                extra_info = {"ScheduleString":ScheduleString,"ArrivingStopJson":json.dumps(end)},
                left_tickets = left_tickets,
                crawl_source = "bjky",
                shift_id='',
            )
            yield LineItem(**attrs)


