#!/usr/bin/python
#-*- coding:utf-8 -*-


import os
import sys
import time
import MySQLdb
import ConfigParser
import schedule
import logging
import os
from config import *
from crawler import Google
from company import COMPANY
from BeautifulSoup import BeautifulSoup
from emailutil import send
from googleplay import GooglePlayAPI
from jianfan import ftoj
import hashlib


reload(sys)
sys.setdefaultencoding("utf-8")


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# 创建handler，用于写入文件
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'log/check_gameid.log')
file_handler = logging.FileHandler(LOGS_DIR.replace(' ','_'))
file_handler.setLevel(logging.DEBUG)
# 创建handler,用于输出到控制台
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
# 定义handler输出格式
formatter = logging.Formatter('%(asctime)-15s %(levelname)s %(message)s')
# formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
cf = ConfigParser.ConfigParser()
cf.read("%s/check_googleplay_games.conf" % dirname)
sections = cf.sections()
#ip_string = os.popen('/sbin/ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6').read()
#ip = ip_string.split()[1].replace('地址:', '')


def gen_label_info_id(game_name):
    """
    根据游戏名生成id,使用sha1,保留8位
    :param game_name:
    """
    if isinstance(game_name, unicode):
        g_name = game_name.encode("utf-8")
    else:
        g_name = game_name
    return hashlib.sha1(g_name.lower()).hexdigest().lower()[:8]


if __name__=="__main__":
    """
        Return the pkg_names in ggzs
        :type ggzs_infos: dict : { pkg_name: { "update_time": update_time,
            "area": [ area, ... ], "company": company } }
        :type game_infos: [ pkg_name, ... ]
    """
    source = {
        'Google官方版': 0,
        'GG官方': 1,
        '高通版': 2,
        '英伟达': 3,
        'PowerVR': 4,
        'Mali': 5,
        '三星': 6
    }
    googleplay_infos = {}
    ip='美国'
    game_infos = []
    db_host = cf.get(ip, "db_host")
    db_port = cf.getint(ip, "db_port")
    db_user = cf.get(ip, "db_user")
    db_pass = cf.get(ip, "db_pass")
    db_data = cf.get(ip, "db_data")
 
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass,
            port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    update_data = []
    try:
        sql = """
        SELECT `area`, `company`, `pkg_name`, `game_name`, `update_time`,
        `game_name_from_google_api` FROM
        `googleplay_games`
        """
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
#        for row in cursor.fetchall():
#            pkg_name = row[2]
#            game_name = row[5]
#            g_name = game_name + u"(GG官方)"
#            game_id = gen_label_info_id(g_name)
#            googleplay_infos[pkg_name] = game_id
        pass

    
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass,
            port=db_port, db='forum', charset='utf8')
    cursor = conn.cursor()
    update_data = []
    try:
        sql = """
        SELECT pkg_name, game_id, market_channel from iplay_game_pkg_info where source=3
        """
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
        for row in cursor.fetchall():
            pkg_name = row[0]
            game_id = row[1]
            market_channel = row[2].encode('utf8')
            import urllib
            import urllib2
            channel = source[market_channel]
            url = 'http://192.168.1.45:8000/cgi-bin/gameid.py?pkgname=%s&channel=%s' % (pkg_name, channel)
            data = urllib2.urlopen(url).read()
            gameid = data.replace('\n', '')
            if gameid == game_id:
                print game_id, gameid, 'success', pkg_name
            else:
                if gameid.find('can not find title') != -1:
                    print game_id, gameid, pkg_name, market_channel
                else:
                    print game_id, gameid, 'Error', pkg_name, market_channel
            

