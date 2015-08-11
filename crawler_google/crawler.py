#!/usr/bin/env python
#-*- coding: utf-8 -*-


"""
File: check_googleplay_games.py
Author: xiangxiaowei
Date: 12/05/14
Description:
"""


import requests
import sys
reload(sys) 
sys.setdefaultencoding( "utf-8" ) 


class Google:
    def __init__(self, referer, host, http_proxie, https_proxie):
        self.referer = referer
        referer = 'https://play.google.com/store/apps/dev?id=6258770168633898802'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/33.0',
            'Referer': referer,
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip',  # 以gzip下载html，降低网络资源负荷
            'Accept-Language': 'zh-cn,en-us;q=0.7,en;q=0.3',
            'Content-Length': '86',
            'Cookie': 'PREF=ID=54d3e46c668f74ce:U=0806b1988518afdd:TM=1411874099:LM=1416486632:S=qv9drTd2LIVCahAX; NID=67=J6fg2e3bnpbDdaN_xcMZXrH7E-VvzYuXKf4jLz-oLWCJ-O_xEzG9JQ2nng236XgOwpm3DCq0JL6m_RIveJM4ASXqy8-7xkuEI-CK4Gz_Imbr3Wt9I8iUvuaf3GwH7pCD; _ga=GA1.3.86026158.1413180514; _gat=1; PLAY_PREFS=CgJVUxD2z9aCnSkosra56Zwp:S:ANO1ljJYk5JjleSs',
            'Host': host,
        }
        self.proxies = {
            "http": http_proxie,
            "https": https_proxie
        }
        self.http_proxie = http_proxie
        self.https_proxie = https_proxie

    def get_game_list(self, url, data):
        result = requests.post(url, headers=self.headers, proxies=self.proxies, data=data, timeout=10)
        content = result.content
        return content

    def get_game_detail(self, url):
        f = requests.post(url, headers=self.headers, proxies=self.proxies, timeout=10)
#        f = requests.post(url, headers=self.headers, timeout=10)
        content = f.content
        return content

    def get_game_id(self, url):
        f = requests.post(url, headers=self.headers, timeout=10)
        content = f.content
        return content

   
