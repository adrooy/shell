#!/usr/bin/env python
#-*- coding: utf-8 -*-


"""
File: check_googleplay_games.py
Author: xiangxiaowei
Date: 12/05/14
Description: 
"""


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
from emailutil import sendMail
from googleplay import GooglePlayAPI
from jianfan import ftoj


reload(sys)
sys.setdefaultencoding("utf-8")


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# 创建handler，用于写入文件
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'log/crawler_game_name.log')
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


def login():
    api = None
    try:
        api = GooglePlayAPI(ANDROID_ID)
        api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)
    except Exception as e:
        logger.debug('login google error %s' % e)
    return api


def get_info(api, pkg_name):
    details = None
    try:
        details = api.details(pkg_name)
    except Exception as e:
        logger.debug('Error in get game_info %s' % e)
    return details


def get_ggzs(ip):
    """
        Return the pkg_names in ggzs
        :type ggzs_infos: list : [ pkg_name, ... ]

    """
    ggzs_infos = []
    db_host = cf.get(ip, "db_host")
    db_port = cf.getint(ip, "db_port")
    db_user = cf.get(ip, "db_user")
    db_pass = cf.get(ip, "db_pass")
    db_data = cf.get(ip, "db_data")
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass,
            port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    try:
        sql = """
        SELECT pkg_name, count(0) FROM `iplay_game_pkg_info` GROUP BY
        pkg_name
        """
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
        for row in cursor.fetchall():
            ggzs_infos.append(row[0])
        cursor.close()
        conn.commit()
        conn.close()
    return ggzs_infos



def get_googleplay(ip):
    """
        Return the pkg_names in ggzs
        :type googleplay_infos: dict : { pkg_name: { "update_time": update_time,
            "area": [ area, ... ], "company": company, "game_name": game_name} }
        :type game_infos: [ pkg_name, ... ]
    """
    googleplay_infos = {}
    game_infos = []
    db_host = cf.get(ip, "db_host")
    db_port = cf.getint(ip, "db_port")
    db_user = cf.get(ip, "db_user")
    db_pass = cf.get(ip, "db_pass")
    db_data = cf.get(ip, "db_data")
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass,
            port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    from datetime import datetime,timedelta
    end_date = datetime.now()
    start_date = str(end_date - timedelta(7)).split(' ')[0].replace('-', '')
    try:
        sql = """
        SELECT `area`, `company`, `pkg_name`, `game_name`, `update_time`,
        `game_name_from_google_api`, `file_size` FROM
        `googleplay_games` WHERE update_time >= '%s'
        """ % start_date
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
        for row in cursor.fetchall():
            area = row[0]
            company = row[1]
            pkg_name = row[2]
            game_name = row[3]
            update_time = int(row[4])
            game_name_from_google_api = row[5]
            file_size = row[6]
            if not game_name_from_google_api and pkg_name not in game_infos:
                game_infos.append(pkg_name)
            if pkg_name not in googleplay_infos:
                info = {
                    "update_time": update_time,
                    "area": [area],
                    "company": company,
                    "game_name": game_name,
                    "file_size": file_size
                }
                googleplay_infos[pkg_name] = info
            else:
                if update_time > googleplay_infos[pkg_name]["update_time"]:
                    googleplay_infos[pkg_name]["update_time"] = update_time
                if file_size:
                    googleplay_infos[pkg_name]["file_size"] = file_size
                googleplay_infos[pkg_name]["area"].append(area)
        cursor.close()
        conn.commit()
        conn.close()
    return googleplay_infos, game_infos


def update_game_name(ip, update_data):
    """
        Return the pkg_names in ggzs
        :type ggzs_infos: dict : { pkg_name: { "update_time": update_time,
            "area": [ area, ... ], "company": company } }
        :type game_infos: [ pkg_name, ... ]
    """
    googleplay_infos = {}
    game_infos = []
    db_host = cf.get(ip, "db_host")
    db_port = cf.getint(ip, "db_port")
    db_user = cf.get(ip, "db_user")
    db_pass = cf.get(ip, "db_pass")
    db_data = cf.get(ip, "db_data")
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass,
            port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    try: 
        sql = """
        UPDATE googleplay_games SET game_name_from_google_api=%(game_name)s
            WHERE pkg_name=%(pkg_name)s
            """
        cursor.executemany(sql, update_data)
    except Exception as e:
        conn.rollback()
    finally:
        cursor.close()
        conn.commit()
        conn.close()
    

def send_email(googleplay_infos, ggzs_infos):
    sorted_games = sorted(googleplay_infos.items(), key=lambda d: int(d[1]['update_time']), reverse=True)
    html = ""
    html += """
        <table style="border:1px solid #ddd">
            <th style="border:1px solid #ddd">游戏名</th>
            <th style="border:1px solid #ddd">厂商</th>
            <th style="border:1px solid #ddd">大小</th>
            <th style="border:1px solid #ddd">游戏包名</th>
            <th style="border:1px solid #ddd">更新时间</th>
            <th style="border:1px solid #ddd">地区</th>
    """
    filename = os.path.join(BASE_DIR, 'GooglePlay各渠道更新游戏汇总.csv')
    with open(filename, 'w') as files:
        files.write('游戏名,厂商,大小,游戏包名,更新时间,地区\n')
        for i in range(len(sorted_games)):
            pkg_name = sorted_games[i][0]
            info = sorted_games[i][1]
            areas = info['area']
            company = info['company']
            update_time = info['update_time']
            game_name = info['game_name']
            file_size = info['file_size'] 
            if not file_size:
                file_size = ''
            if pkg_name not in ggzs_infos:
                result = [game_name.replace(',', '.'), company.replace(',', '.'), file_size, 'https://play.google.com/store/apps/details?id=%s' % pkg_name, str(update_time), ';'.join(areas)]
                files.write('%s\n' % ','.join(result))
                html += """
                    <tr>
                        <td style="border:1px solid #ddd">%s</td>
                        <td style="border:1px solid #ddd">%s</td>
                        <td style="border:1px solid #ddd">%s</td>
                        <td style="border:1px solid #ddd"><a href="https://play.google.com/store/apps/details?id=%s">%s</td>
                        <td style="border:1px solid #ddd">%s</td>
                        <td style="border:1px solid #ddd">%s</td>
                    </tr>
                """ % (game_name, company, file_size, pkg_name, pkg_name, str(update_time), ';'.join(areas))
        html += """
            </table>
        """
    if html:
        sendMail('GooglePlay各渠道更新游戏汇总', html, filename)


def crawler(game_infos):
    update_data = []
    for pkg_name in game_infos:
        try:
            api = login()
            info = get_info(api, pkg_name)
            info = api.toDict(info)
            info = str(info)
            info = info.replace("true", "True")
            info = info.replace("false", "False")
            info = eval(str(info))
            doc = info["docV2"]
            game_name = doc["title"]
            game_name = ftoj(game_name)
            info = {
                "pkg_name": pkg_name,
                "game_name": game_name
            }
            update_data.append(info)
        except Exception as e:
            logger.debug("%s crawler error %s" % (pkg_name, e))
    return update_data


if __name__=='__main__':
    logger.debug("\n\n")
    logger.debug("START get game_name")
    ggzs_infos = get_ggzs("ggzs")
    googleplay_infos, game_infos = get_googleplay("美国")
    send_email(googleplay_infos, ggzs_infos)
#    print len(game_infos)
#    update_data = crawler(game_infos)
    logger.debug("END get game_name")
#    update_game_name("美国", update_data)
