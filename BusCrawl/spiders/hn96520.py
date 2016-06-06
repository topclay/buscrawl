#!/usr/bin/env python
# encoding: utf-8

import scrapy
import json
import datetime
import urllib
from bs4 import BeautifulSoup as bs
import re
# from fabric.colors import green, red
from cchardet import detect


from datetime import datetime as dte
from BusCrawl.item import LineItem
from BusCrawl.utils.tool import get_pinyin_first_litter
from base import SpiderBase
from scrapy.conf import settings
from pymongo import MongoClient
import ipdb

cityZD = [{"City":"郑州市","ZD":[{"DM":"410101","Name":"郑州中心站"},{"DM":"410109","Name":"郑州总站"},{"DM":"410106","Name":"高铁枢纽站"},{"DM":"410108","Name":"郑州西站"},{"DM":"410120","Name":"郑州南站"},{"DM":"410107","Name":"郑州北站"},{"DM":"410121","Name":"郑州陇海站"},{"DM":"410122","Name":"郑州七里河站"},{"DM":"410114","Name":"郑汴路汽车站"},{"DM":"410112","Name":"上街汽车站"},{"DM":"410111","Name":"荥阳汽车站"},{"DM":"410116","Name":"登封城乡站"},{"DM":"410113","Name":"新郑汽车站"},{"DM":"410102","Name":"新密中心站"},{"DM":"410117","Name":"中牟汽车站"},{"DM":"410123","Name":"巩义汽车站"},{"DM":"410115","Name":"新密长途汽车站"},{"DM":"410110","Name":"登封汽车站"}]},{"City":"漯河市","ZD":[{"DM":"411101","Name":"漯河汽车站"},{"DM":"411104","Name":"漯河汽车西站"},{"DM":"411103","Name":"恒通汽车站"},{"DM":"411105","Name":"舞阳汽车站"},{"DM":"411106","Name":"临颍汽车站"},{"DM":"411107","Name":"临颍中心站"}]},{"City":"开封市","ZD":[{"DM":"410202","Name":"开封中心站"},{"DM":"410204","Name":"宋城路站"},{"DM":"410201","Name":"开封西站"},{"DM":"410208","Name":"通许汽车站"},{"DM":"410209","Name":"尉氏汽车站"},{"DM":"410207","Name":"杞县汽车站"},{"DM":"410206","Name":"兰考汽车站"}]},{"City":"安阳市","ZD":[{"DM":"410501","Name":"安阳汽车中心站"},{"DM":"410507","Name":"安阳客运东站"},{"DM":"410512","Name":"滑县汽车站"},{"DM":"410506","Name":"林州汽车南站"},{"DM":"410504","Name":"林州汽车北站"},{"DM":"410510","Name":"汤阴汽车站"},{"DM":"410503","Name":"安阳汽车西站"}]},{"City":"焦作市","ZD":[{"DM":"410801","Name":"焦作客运总站"},{"DM":"410802","Name":"焦作旅游中心站"},{"DM":"410809","Name":"温县中心站"},{"DM":"410803","Name":"修武县总站"},{"DM":"410810","Name":"武陟汽车站"},{"DM":"410808","Name":"温县客车站"},{"DM":"410811","Name":"武陟客运总站"},{"DM":"410807","Name":"沁阳汽车站"},{"DM":"410806","Name":"博爱客车站"},{"DM":"410805","Name":"孟州汽车站"}]},{"City":"洛阳市","ZD":[{"DM":"410301","Name":"洛阳汽车站"},{"DM":"410304","Name":"洛阳锦远汽车站"},{"DM":"410310","Name":"洛宁汽车站"},{"DM":"410312","Name":"宜阳汽车站"},{"DM":"410314","Name":"汝阳汽车站"},{"DM":"410309","Name":"偃师汽车站"},{"DM":"410313","Name":"嵩县汽车站"},{"DM":"410307","Name":"孟津汽车站"},{"DM":"410311","Name":"新安汽车站"},{"DM":"410315","Name":"栾川汽车站"}]},{"City":"新乡市","ZD":[{"DM":"410704","Name":"新乡客运总站"},{"DM":"410714","Name":"长垣客运总站"},{"DM":"410710","Name":"新乡汽车东站"},{"DM":"410713","Name":"长垣汽车站"},{"DM":"410706","Name":"辉县汽车站"},{"DM":"410709","Name":"卫辉汽车站"}]},{"City":"驻马店","ZD":[{"DM":"411701","Name":"驻马店中心站"},{"DM":"411702","Name":"驻马店客运东站"},{"DM":"411710","Name":"上蔡汽车（东）站"},{"DM":"411719","Name":"驻马店西站"},{"DM":"411720","Name":"西平汽车站"},{"DM":"411721","Name":"上蔡汽车站"},{"DM":"411718","Name":"新蔡汽车站"},{"DM":"411717","Name":"新蔡新汽车站"},{"DM":"411722","Name":"平舆汽车站"},{"DM":"411723","Name":"汝南汽车站"},{"DM":"411724","Name":"泌阳汽车站"},{"DM":"411705","Name":"正阳汽车站"},{"DM":"411725","Name":"确山汽车站"},{"DM":"411726","Name":"遂平汽车站"},{"DM":"411712","Name":"平舆运蓬北站"}]},{"City":"许昌市","ZD":[{"DM":"411001","Name":"许昌中心站"},{"DM":"411002","Name":"许昌汽车南站"},{"DM":"411007","Name":"禹州第一汽车站"},{"DM":"411005","Name":"鄢陵西站"},{"DM":"411010","Name":"许昌汽车东站"},{"DM":"411003","Name":"鄢陵陵南客运站"}]},{"City":"平顶山","ZD":[{"DM":"410401","Name":"平顶山中心站"},{"DM":"410402","Name":"平顶山长途站"},{"DM":"410405","Name":"鲁山长途站"},{"DM":"410406","Name":"鲁山汽车站"},{"DM":"410408","Name":"郏县鹰运站"},{"DM":"410410","Name":"叶县汽车总站"},{"DM":"410414","Name":"舞钢长途站"},{"DM":"410404","Name":"宝丰汽车站"},{"DM":"410409","Name":"郏县贺翔站"},{"DM":"410412","Name":"汝州中心站"},{"DM":"410413","Name":"汝州长途站"}]},{"City":"鹤壁市","ZD":[{"DM":"410601","Name":"淇滨客运总站"},{"DM":"410602","Name":"鹤壁长风站"},{"DM":"410604","Name":"鹤壁枢纽站"},{"DM":"410606","Name":"淇县汽车站"}]},{"City":"济源市","ZD":[{"DM":"410881","Name":"济源总站"},{"DM":"410882","Name":"济源老公交站"}]},{"City":"南阳市","ZD":[{"DM":"411301","Name":"南阳汽车站（西站）"},{"DM":"411303","Name":"南阳东站"},{"DM":"411304","Name":"南阳南站"},{"DM":"411302","Name":"南阳商城站"},{"DM":"411311","Name":"新野汽车站"},{"DM":"411305","Name":"宛运镇平站"},{"DM":"411306","Name":"内乡汽车站"},{"DM":"411307","Name":"西峡汽车站"},{"DM":"411308","Name":"南召汽车站"},{"DM":"411321","Name":"邓州汽车站"},{"DM":"411320","Name":"唐河汽车站"},{"DM":"411309","Name":"云阳客运站"},{"DM":"411322","Name":"方城汽车站"},{"DM":"411314","Name":"社旗汽车站"},{"DM":"411319","Name":"镇平通运站"},{"DM":"411315","Name":"淅川汽车站"},{"DM":"411323","Name":"桐柏汽车站"}]},{"City":"濮阳市","ZD":[{"DM":"410901","Name":"濮阳长途汽车站"},{"DM":"410902","Name":"濮阳飞龙站"},{"DM":"410909","Name":"濮阳东方站（总站）"},{"DM":"410908","Name":"台前汽车站"}]},{"City":"三门峡","ZD":[{"DM":"411201","Name":"三门峡汽车总站"},{"DM":"411207","Name":"卢氏汽车站"},{"DM":"411203","Name":"灵宝汽车站"}]},{"City":"商丘市","ZD":[{"DM":"411401","Name":"商丘中心汽车站"},{"DM":"411405","Name":"夏邑客运总站"},{"DM":"411408","Name":"柘城汽车站"},{"DM":"411415","Name":"民权汽车站"},{"DM":"411416","Name":"永城汽车站"},{"DM":"411412","Name":"商丘万里客运站"},{"DM":"411601","Name":"永城中心站"},{"DM":"411418","Name":"宁陵汽车站"}]},{"City":"周口市","ZD":[{"DM":"411602","Name":"周口市中心站"},{"DM":"411603","Name":"太康汽车站"},{"DM":"411604","Name":"沈丘汽车站"},{"DM":"411606","Name":"郸城汽车站"},{"DM":"411607","Name":"扶沟长途汽车站"},{"DM":"411609","Name":"西华汽车站"},{"DM":"411610","Name":"淮阳汽车站"},{"DM":"411612","Name":"周口客运总站"},{"DM":"411613","Name":"鹿邑客运西站"}]},{"City":"信阳市","ZD":[{"DM":"411501","Name":"信阳汽车站"},{"DM":"411510","Name":"信阳新华路汽车站"},{"DM":"411505","Name":"潢川汽车站"},{"DM":"411502","Name":"光山汽车站"},{"DM":"411504","Name":"息县汽车站"},{"DM":"411506","Name":"淮滨汽车站"},{"DM":"411508","Name":"固始汽车站"},{"DM":"411507","Name":"商城汽车站"},{"DM":"411503","Name":"罗山汽车站"}]}]
db_config = settings.get("MONGODB_CONFIG")
city = MongoClient(db_config["url"])[db_config["db"]]['hn96520city']


class HnSpider(SpiderBase):
    name = "hn96520"
    custom_settings = {
        "ITEM_PIPELINES": {
            'BusCrawl.pipeline.MongoPipeline': 300,
        },

        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'BusCrawl.middleware.BrowserRandomUserAgentMiddleware': 400,
            'BusCrawl.middleware.ProxyMiddleware': 410,
            # 'BusCrawl.middleware.TongChengHeaderMiddleware': 410,
        },
        "DOWNLOAD_DELAY": 0.75,
        # "RANDOMIZE_DOWNLOAD_DELAY": True,
    }
    dcitys = city.find()
    # base_url = "http://www.hn96520.com/default.aspx"
    base_url = 'http://www.hn96520.com/ajax/query.aspx?method=GetListByPY&q=b&limit=20&timestamp=1465204637302&global=410101'
    #base_url = 'http://www.hn96520.com/placeorder.aspx?start=%E9%83%91%E5%B7%9E%E4%B8%AD%E5%BF%83%E7%AB%99&global=410101&end=%E6%9D%AD%E5%B7%9E&date=2016-05-30'

    def start_requests(self):
        urls = []
        qtimes = []
        dcitys = self.dcitys
        for x in cityZD:
            for y in x.get('ZD'):
                for z in dcitys:
                    dcity = z.get('mc', '')
                    url = 'http://www.hn96520.com/placeorder.aspx?start={0}&global={1}&end={2}&date=--{3}'.format(y.get('Name'), y.get('DM'), dcity, x.get('City'))
                    urls.append(url)
        for i in xrange(7):
            qtime = (datetime.datetime.now() +
                     datetime.timedelta(i)).strftime("%Y-%m-%d")
            qtimes.append(qtime)
        urls = list(set(urls))
        for j in qtimes:
            for k in urls:
                url = k.split('--')[0] + j
                city = k.split('--')[1]
                yield scrapy.Request(url, callback=self.parse_line, meta={'city': city})

        # 初始化抵达城市
        # dcitys = 'abcdefghijklmnopqrstuvwxyz'
        # for city in dcitys:
        #     url = 'http://www.hn96520.com/ajax/query.aspx?method=GetListByPY&q={0}&limit=1000&global=410101'.format(city)
        #     yield scrapy.Request(url, callback=self.parse_dcity)

    # 初始化到达城市
    def parse_dcity(self, response):
        soup = json.loads(response.body)
        for x in soup:
            data = x.get('data', {})
            if city.find({'py': data['py']}).count() <= 0:
                city.save(dict(data))
        # print(soup)

    def parse(self, response):
        soup = bs(response.body, 'lxml')
        info = soup.find_all(
            'div', attrs={'id': re.compile(r"divHotline\_\d+")})
        # print(info)
        urls = []
        qtimes = []
        for x in info:
            try:
                y = x.find_all('a')
                for z in y:
                    url = 'http://www.hn96520.com/' + z.get('href')
                    # print(url)
                    urls.append(url.strip())
            except Exception as e:
                print(e)
        urls = list(set(urls))
        # for url in urls:
        #     for x in cityZD:
        #         for y in x.get('ZD'):
        #              name =  urllib.unquote(url.split('&')[0].split('=')[-1])
        #              dm = url.split('&')[1].split('=')[-1]
        #              pk = {'DM': dm, 'Name': name}
        #              if pk == y:
        #                 city = x.get('City')
        # print(red(len(urls)))
        for i in xrange(7):
            qtime = (datetime.datetime.now() +
                     datetime.timedelta(i)).strftime("%Y-%m-%d")
            qtimes.append(qtime)
        # print(qtimes)
        for j in qtimes:
            for k in urls:
                url = k[:-10] + j
                for x in cityZD:
                    for y in x.get('ZD'):
                         name =  urllib.unquote(url.split('&')[0].split('=')[-1])
                         dm = url.split('&')[1].split('=')[-1]
                         pk = {'DM': dm, 'Name': name}
                         if pk == y:
                            city = x.get('City')
                            # print(city)
                            yield scrapy.Request(url, callback=self.parse_line, meta={'city': city})

    def parse_line(self, response):
        # from pprint import pprint
        # print(green('Staring {0}'.format(response.url)))
        s_city_name = response.meta['city'].decode('utf-8')
        soup = bs(response.body, 'lxml')
        info = soup.find('table', attrs={'class': 'resulttb'}).find_all(
            'tbody', attrs={'class': 'rebody'})
        for x in info:
            try:
                bus_num = x.find(
                    'td', attrs={'align': 'center'}).get_text().strip()
                s_sta_name = x.find_all(
                    'td')[1].get_text().split()[0]
                d_city_name = x.find_all('td')[1].get_text().split()[1]
                drv_date = x.find_all('td')[2].get_text().strip()
                drv_time = x.find_all('td')[3].get_text().strip()
                d_sta_name = x.find_all('td')[4].get_text().strip()
                distance = x.find_all('td')[5].get_text().strip()
                vehicle_type = x.find_all('td')[6].get_text().strip()
                full_price = x.find_all('td')[7].get_text().strip()
                left_tickets = int(x.find_all('td')[8].get_text().strip())
                y = x.find_all('td')[9].a.get('href').split('?')[-1]
                extra = {}
                for z in y.split('&'):
                    extra[z.split('=')[0]] = z.split('=')[1]

                attrs = dict(
                    s_province='河南',
                    s_city_id="",
                    s_city_name=s_city_name,
                    s_sta_name=s_sta_name,
                    s_city_code=get_pinyin_first_litter(s_city_name),
                    s_sta_id='',
                    d_city_name=d_city_name,
                    d_city_id="",
                    d_city_code=get_pinyin_first_litter(d_city_name),
                    d_sta_id="",
                    d_sta_name=d_sta_name,
                    drv_date=drv_date,
                    drv_time=drv_time,
                    drv_datetime=dte.strptime("%s %s" % (
                        drv_date, drv_time), "%Y-%m-%d %H:%M"),
                    distance=unicode(distance),
                    vehicle_type=vehicle_type,
                    seat_type="",
                    bus_num=bus_num,
                    full_price=float(full_price),
                    half_price=float(full_price) / 2,
                    fee=0.0,
                    crawl_datetime=dte.now(),
                    extra_info=extra,
                    left_tickets=left_tickets,
                    crawl_source="hn96520",
                    shift_id="",
                )
                # pprint(attrs)
                yield LineItem(**attrs)

            except Exception as e:
                print(e)
