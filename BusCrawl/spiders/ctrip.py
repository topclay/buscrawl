# -*- coding: utf-8 -*-
import scrapy
import json
import urllib
import datetime

from datetime import datetime as dte
from BusCrawl.item import LineItem
from base import SpiderBase
from BusCrawl.utils.tool import get_pinyin_first_litter


class CTripSpider(SpiderBase):
    name = "ctrip"
    custom_settings = {
        "ITEM_PIPELINES": {
            'BusCrawl.pipeline.MongoPipeline': 300,
        },

        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'BusCrawl.middleware.MobileRandomUserAgentMiddleware': 400,
            'BusCrawl.middleware.ProxyMiddleware': 410,
            'BusCrawl.middleware.CtripHeaderMiddleware': 410,
        },
        "DOWNLOAD_DELAY": 0.2,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
    }
    base_url = "http://m.ctrip.com/restapi/busphp/app/index.php"

    def start_requests(self):
        # 这是个pc网页页面
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/47.0.2526.106 Safari/537.36"}
        web_page = "http://qiche.tieyou.com/index.php?param=/ajax/cityList"
        return [scrapy.Request(web_page, headers=headers, callback=self.parse_start_city)]

    def parse_start_city(self, response):
        res = json.loads(response.body[1:-1])
        params = dict(
            param="/api/home",
            method="product.getToCityList",
            ref="ctrip.h5",
            partner="ctrip.app",
            clientType="Android--hybrid",
            vendor="",
            fromCity="",
            contentType="json",
        )
        for pro in res['hotFromCity']['province']:
            province = pro["province_name"]
            if not province or not self.is_need_crawl(province=province):
                continue
            self.logger.info("start province: %s" % province)

            for ci in pro["citys"]:
                d = {
                    "province": province,
                    "name": ci,
                }
                if not self.is_need_crawl(city=ci):
                    continue
                self.logger.info("start province: %s city: %s", province, ci)
                params.update(fromCity=ci)
                url = "%s?%s" % (self.base_url, urllib.urlencode(params))
                yield scrapy.Request(url, callback=self.parse_target_city, meta={"start": d})

    def parse_target_city(self, response):
        res = json.loads(response.body)
        if int(res["code"]) != 1:
            self.logger.error("parse_target_city: Unexpected return, %s" % res["message"])
            return

        start = response.meta["start"]
        for tar in res["return"]:
            d = {
                "name": tar["name"],
            }

            today = datetime.date.today()
            for i in range(1, 10):
                sdate = str(today+datetime.timedelta(days=i))
                if self.has_done(start["name"], d["name"], sdate):
                    #self.logger.info("ignore %s ==> %s %s" % (start["name"], d["name"], sdate))
                    continue
                params = dict(
                    param="/api/home",
                    method="product.getBusList",
                    v="1.0",
                    ref="ctrip.h5",
                    partner="ctrip.app",
                    clientType="Android--hybrid",
                    fromCity=start["name"],
                    toCity=d["name"],
                    fromDate=sdate,
                    contentType="json",
                )
                url = "%s?%s" % (self.base_url, urllib.urlencode(params))
                yield scrapy.Request(url, callback=self.parse_line, meta={"start": start, "end": d, "drv_date": sdate})

    def parse_line(self, response):
        "解析班车"
        try:
            res = json.loads(response.body)
        except Exception, e:
            print response.body
            raise e
        start = response.meta["start"]
        end = response.meta["end"]
        drv_date = response.meta["drv_date"]
        self.mark_done(start["name"], end["name"], drv_date)
        if int(res["code"]) != 1:
            #self.logger.error("parse_line: Unexpected return, %s" % str(res))
            return
        for d in res["return"]:
            if not d["bookable"]:
                continue
            if d["busType"] == "流水班":
                continue
            from_station = unicode(d["fromStationName"])
            to_station = unicode(d["toStationName"])
            ticket_info = d["showTicketInfo"]
            if ticket_info == "有票":
                left_tickets = 45
            elif ticket_info.endswith("张"):
                left_tickets = int(ticket_info[:-1])
            elif ticket_info == "预约购票":
                continue
            else:
                print ticket_info, d["bookable"]
                1/0

            attrs = dict(
                s_province = start["province"],
                s_city_name = d["fromCityName"],
                s_city_id="",
                s_city_code=get_pinyin_first_litter(d["fromCityName"]),
                s_sta_name = from_station,
                s_sta_id="",
                d_city_name = d["toCityName"],
                d_city_id="",
                d_city_code=get_pinyin_first_litter(d["toCityName"]),
                d_sta_name = to_station,
                d_sta_id="",
                drv_date = drv_date,
                drv_time = d["fromTime"],
                drv_datetime = dte.strptime("%s %s" % (drv_date, d["fromTime"]), "%Y-%m-%d %H:%M"),
                distance = "0",
                vehicle_type = d["busType"],
                seat_type = "",
                bus_num = d["busNumber"],
                full_price = float(d["fullPrice"]),
                half_price = float(d["fullPrice"])/2,
                fee = 0,
                crawl_datetime = dte.now(),
                extra_info = {},
                left_tickets = left_tickets,
                crawl_source = "ctrip",
                shift_id="",
            )
            yield LineItem(**attrs)
