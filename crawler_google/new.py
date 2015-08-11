#!/usr/bin/env python
#-*- coding: utf-8 -*-


"""
File: check_googleplay_games.py
Author: xiangxiaowei
Date: 12/05/14
Description: 
"""


import re
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


reload(sys)
sys.setdefaultencoding("utf-8")

GAME = [
    'Dungeon Hunters',
    'GloftD5HM',
    '地牢猎手',
    '玩具堡',
    'toys burg',
    'angrymobgames',
    'toysburg',
    '杀戮之旅',
    'overkill',
    'craneballs',
    '时空水晶',
    '時空ノ水晶',
    '神奇之树',
    '最后梦想家',
    'Almightree',
    '极品飞车',
    '无极限',
    'Need For Speed',
    'No Limits'
]

COUNT_BY_STEP = 24

dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
cf = ConfigParser.ConfigParser()
cf.read("%s/check_googleplay_games.conf" % dirname)
sections = cf.sections()
#ip_string = os.popen('/sbin/ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6').read()
#ip = ip_string.split()[1].replace('地址:', '')
ip = "测试"
db_host = cf.get(ip, "db_host")
db_port = cf.getint(ip, "db_port")
db_user = cf.get(ip, "db_user")
db_pass = cf.get(ip, "db_pass")
db_data = cf.get(ip, "db_data")
host = cf.get(ip, "host")
referer = cf.get(ip, "referer")
http_proxie = cf.get(ip, "http_proxie")
https_proxie = cf.get(ip, "https_proxie")
area = cf.get(ip, "area")


def login(logger):
    api = None
    try:
        api = GooglePlayAPI(ANDROID_ID)
        api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)
    except Exception as e:
        logger.debug('login google error %s' % e)
    return api


def get_info(api, pkg_name, logger):
    details = None
    try:
        details = api.details(pkg_name)
    except Exception as e:
        logger.debug('Error in get game_info %s' % e)
    return details


def get_date():
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return date


def update_data(games_to_insert, games_to_update, logger, db_host, db_user, db_pass, db_data, db_port):
    infos = []
    for key in games_to_insert:
        key_info = key.split('<>')
        area = key_info[0]
        company = key_info[1]
        pkg_name = key_info[2]
        game_name = games_to_insert[key]['game_name']
        update_time = games_to_insert[key]['update_time']
        file_size = games_to_insert[key]['file_size']
        info = [area, company, pkg_name, game_name, update_time, file_size]
        infos.append(info)
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    try: 
        sql = """
        INSERT INTO googleplay_games(
                area,
                company,
                pkg_name,
                game_name,
                update_time,
                file_size
                ) VALUES(
                %s
                , %s
                , %s
                , %s
                , %s
                , %s
                )
            """
        cursor.executemany(sql, infos)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.debug('error in insert data; %s; %s; %s' % (e, pkg_name, game_name))
    finally:
        cursor.close()
        conn.close()
        logger.debug('success insert %d games' % len(games_to_insert))
    infos = []
    for key in games_to_update:
        key_info = key.split('<>')
        area = key_info[0]
        company = key_info[1]
        pkg_name = key_info[2]
        game_name = games_to_update[key]['game_name']
        update_time = games_to_update[key]['update_time']
        info = [update_time, area, company, pkg_name]
        infos.append(info)
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    try: 
        sql = """
        UPDATE googleplay_games SET update_time=%s
            WHERE area=%s and company=%s and pkg_name=%s
            """
        cursor.executemany(sql, infos)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.debug('error in update data; %s; %s; %s' % (e, pkg_name, game_name))
    finally:
        cursor.close()
        conn.close()
        logger.debug('success update %d games' % len(games_to_update))
    

def get_games(logger, db_host, db_user, db_pass, db_data, db_port):
    games_in_db = {}
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()

    cursor.execute('SELECT `area`, `company`, `pkg_name`, `game_name`, `update_time` FROM googleplay_games')
    curs = cursor.fetchall()
    for cur in curs:
        areas = cur[0]
        company = cur[1]
        pkg_name = cur[2]
        game_name = cur[3]
        update_time = cur[4]
        key = ('%s<>%s<>%s' % (areas, company, pkg_name)).encode('utf-8')
        if key in games_in_db:
            logger.debug('error')
        else:
            info = {
                "update_time": update_time,
                "game_name": game_name
            }
            games_in_db[key] = info
    conn.commit()
    conn.close()
    return games_in_db


def send_email(games_to_insert, games_to_update, logger, Totle):
    key_games = {}
    html = ""
    for key in games_to_insert:
        info = key.split("<>")
        areas = info[0]
        company = info[1]
        pkg_name = info[2]
        game_name = games_to_insert[key]['game_name']
        for game_key in GAME:
            if re.match(game_key, pkg_name, flags=re.I) or re.match(game_key, game_name, flags=re.I):
                key_games[key] = games_to_insert[key]
    for key in games_to_update:
        info = key.split("<>")
        areas = info[0]
        company = info[1]
        pkg_name = info[2]
        game_name = games_to_update[key]['game_name']
        for game_key in GAME:
            if re.match(game_key, pkg_name, flags=re.I) or re.match(game_key, game_name, flags=re.I):
                key_games[key] = games_to_update[key]
    if key_games:
        sorted_games = sorted(key_games.items(), key=lambda d: int(d[1]['update_time']), reverse=True)
    else:
        sorted_games = []
    html += """
        <p>共抓取%d个游戏</p>
        <p>共抓取%d个重点游戏</p>
        <table style="border:1px solid #ddd">
            <th style="border:1px solid #ddd">地区</th>
            <th style="border:1px solid #ddd">厂商</th>
            <th style="border:1px solid #ddd">游戏名</th>
            <th style="border:1px solid #ddd">大小</th>
            <th style="border:1px solid #ddd">游戏包名</th>
            <th style="border:1px solid #ddd">更新时间</th>
    """ % (len(Totle), len(key_games))
    for i in range(len(sorted_games)):
        key = sorted_games[i][0]
        info = key.split("<>")
        areas = info[0]
        company = info[1]
        pkg_name = info[2]
        game_name = sorted_games[i][1]["game_name"]
        update_time = sorted_games[i][1]["update_time"]
        file_size = sorted_games[i][1]["file_size"]
        html += """
            <tr>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd"><a href="https://play.google.com/store/apps/details?id=%s">%s</td>
                <td style="border:1px solid #ddd">%s</td>
            </tr>
        """ % (areas, company, game_name, file_size, pkg_name, pkg_name, update_time)
    html += """
        </table>
    """
    html += """<br>"""
    if games_to_insert:
        sorted_games = sorted(games_to_insert.items(), key=lambda d: int(d[1]['update_time']), reverse=True)
    else:
        sorted_games = []
    html += """
        <p>共抓取%d个新游戏</p>
        <table style="border:1px solid #ddd">
            <th style="border:1px solid #ddd">地区</th>
            <th style="border:1px solid #ddd">厂商</th>
            <th style="border:1px solid #ddd">游戏名</th>
            <th style="border:1px solid #ddd">大小</th>
            <th style="border:1px solid #ddd">游戏包名</th>
            <th style="border:1px solid #ddd">更新时间</th>
    """ % len(games_to_insert)
    for i in range(len(sorted_games)):
        key = sorted_games[i][0]
        info = key.split("<>")
        areas = info[0]
        company = info[1]
        pkg_name = info[2]
        game_name = sorted_games[i][1]["game_name"]
        update_time = sorted_games[i][1]["update_time"]
        file_size = sorted_games[i][1]["file_size"]
        html += """
            <tr>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd"><a href="https://play.google.com/store/apps/details?id=%s">%s</td>
                <td style="border:1px solid #ddd">%s</td>
            </tr>
        """ % (areas, company, game_name, file_size, pkg_name, pkg_name, update_time)
    html += """
        </table>
    """
    html += """<br>"""
    if games_to_update:
        sorted_games = sorted(games_to_update.items(), key=lambda d: int(d[1]['update_time']), reverse=True)
    else:
        sorted_games = []
    html += """
        <p>共更新%d个游戏</p>
        <table style="border:1px solid #ddd">
            <th style="border:1px solid #ddd">地区</th>
            <th style="border:1px solid #ddd">厂商</th>
            <th style="border:1px solid #ddd">游戏名</th>
            <th style="border:1px solid #ddd">大小</th>
            <th style="border:1px solid #ddd">游戏包名</th>
            <th style="border:1px solid #ddd">更新时间</th>
    """ % len(games_to_update)
    for i in range(len(sorted_games)):
        key = sorted_games[i][0]
        info = key.split("<>")
        areas = info[0]
        company = info[1]
        pkg_name = info[2]
        game_name = sorted_games[i][1]["game_name"]
        update_time = sorted_games[i][1]["update_time"]
        file_size = sorted_games[i][1]["file_size"]
        html += """
            <tr>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd">%s</td>
                <td style="border:1px solid #ddd"><a href="https://play.google.com/store/apps/details?id=%s">%s</td>
                <td style="border:1px solid #ddd">%s</td>
            </tr>
        """ % (areas, company, game_name, file_size, pkg_name, pkg_name, update_time)
    html += """
        </table>
    """
    if html:
        send('GooglePlay更新的游戏(%s)' % area, html)


def job():
    date = get_date()
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # 创建handler，用于写入文件
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    LOGS_DIR = 'crawler_%s.log' % str(int(time.time()))
    log_date = get_date().split(' ')[0]
    LOGS_DIR = 'crawler_%s.log' % str(log_date)
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
#    schedule.every(10).minutes.do(job)
#    schedule.every().hour.do(job)
#    schedule.every().day.at("10:30").do(job)
#    schedule.every().monday.do(job)
#    schedule.every().wednesday.at("13:15").do(job)
    logger.debug('START %s' % get_date())
    logger.debug("running from %s" % dirname)
    logger.debug("file is %s" % filename)
    logger.debug("ip is %s" % ip)
#修改conf文件的内容
#cf.set("db", "db_pass", "111111")
#cf.write(open("test.conf", "w"))
    logger.debug("db_port is %s" % db_port)
    logger.debug("db_user is %s" % db_user)
    logger.debug("db_pass is %s" % db_pass)
    logger.debug("db_data is %s" % db_data)
    logger.debug("host is %s" % host)
    logger.debug("referer is %s" % referer)
    logger.debug("http_proxie is %s" % http_proxie)
    logger.debug("https_proxie is %s" % https_proxie)
    logger.debug("area is %s" % area)
    logger.debug("has %d companys" % len(COMPANY))

#    games_in_db = get_games(logger, db_host, db_user, db_pass, db_data, db_port)
    games_to_email = {}
    games_to_insert = {}
    games_to_update = {}
    Totle = {}
#    logger.debug("has %d games in db"  % len(games_in_db))
    logger.debug('crawler start')
    #try:
    if 1==1:
        google = Google(referer, host, http_proxie, https_proxie)
#        for company in COMPANY:
        if 1==1:
            company = 'Gameloft'
            if 1==1:
    #        try:
                'token="GAEiAggK:S:ANO1ljLXX6E"'
                company_url = 'https://%s/store/apps/developer?id=%s' % (host, company)
 
                company_url = 'https://play.google.com/store/apps/dev?id=6258770168633898802'
                content = google.get_game_detail(company_url)
                token_mid = r'token="([\w]{8}:S:[\w]{11})"'
                token = re.findall(token_mid, content)[0]
                num = 1
                pkg_names = []
                tokens = [token]
                #while True:
                for i in range(1, 10):
                    print token, num, len(pkg_names)
                    data = {
                        'pageNum': num,
                        'sp': 'CAF6LxIOCghHYW1lbG9mdBAIGANKHWlubGluZTtkZXZlbG9wZXJwYWdlOmZlYXR1cmVkgAEA:S:ANO1ljJJNAg',
                        'pagTok': token,
                        'xhr': 1
                    }
                    post_url = 'https://play.google.com/store/xhr/searchcontent?authuser=0'
                    content = google.get_game_list(post_url, data)
                    r_mid = r'/store/apps/details\?id\\u003d[\w+\.]+\w+'
                    links = re.findall(r_mid, content)
                    for link in links:
                        pkg_name = link.split('\\u003d')[1]
                        if pkg_name not in pkg_names:
                            pkg_names.append(pkg_name)
                    token_mid = r'"([\w]{8}:S:[\w]{11})"'
                    token = re.findall(token_mid, content)[0] if re.findall(token_mid, content) else ''
                    num += 1
                    #if token == '':
                    #	break
                    tokens.append(token)
                print len(pkg_names)
                print tokens

                '''
                for i in range(1, 100):
                    num = COUNT_BY_STEP * i
                    content = google.get_game_list(company_url, num)
                    soup = BeautifulSoup(content)
                    games = soup.findAll("a", {"class": "title"})
                    if len(games) < num:
                        break
                if content:
                    games = soup.findAll("a", {"class": "title"})
                    logger.debug("%s has %d games" % (company, len(games)))
                    for game in games:
                        pkg_name = game['href'].split('details?id=')[1].encode('utf-8')
                        game_name = game['title'].encode('utf-8')
                        game_url = 'https://%s/store/apps/details?id=%s&lb=ch' % (host, pkg_name)
                        detail = google.get_game_detail(game_url)
                        try:
                            if detail:
                                soup = BeautifulSoup(detail)
                                try:
                                    file_size = soup.find("div", {"itemprop": "fileSize"}).string.replace(' ', '').encode('utf-8')
                                except:
                                    file_size = ''
                                a = soup.find("div", {"class": "document-subtitle"})
                                try:
                                    y = a.string.split('- ')[1].split('年')[0]
                                    m = a.string.split('- ')[1].split('年')[1].split('月')[0]
                                    d = a.string.split('- ')[1].split('年')[1].split('月')[1].split('日')[0]
                                    update_time = ('%s%s%s' % (y.zfill(4), m.zfill(2), d.zfill(2))).encode('utf-8')
                                except: 
                                    y = a.string.encode('utf-8').decode('gbk').split('- ')[1].split('暮拧麓')[0]
                                    m = a.string.encode('utf-8').decode('gbk').split('- ')[1].split('暮拧麓')[1].split('膰&oelig;&circ;')[0]
                                    d = a.string.encode('utf-8').decode('gbk').split('- ')[1].split('暮拧麓')[1].split('膰&oelig;&circ;')[1].split('膰&mdash;慕')[0]
                                    update_time = ('%s%s%s' % (y.zfill(4), m.zfill(2), d.zfill(2))).encode('gbk')
                                key = '%s<>%s<>%s' % (area, company, pkg_name)
                                info = {
                                    "update_time": update_time,
                                    "game_name": game_name,
                                    "file_size": file_size
                                }
                                if key not in games_in_db:
                                    games_to_email[key] = info
                                    games_to_insert[key] = info
                                else:
                                    if int(games_in_db[key]["update_time"]) != int(update_time):
                                        games_to_email[key] = info
                                        games_to_update[key] = info
                                Totle[key] = info
                        except Exception as e:
                            logger.debug('error in update_time %s, %s' % (e, pkg_name))
                    logger.debug('%s %s %s %s' % (game_name, pkg_name, update_time, company))
                '''
                logger.debug('end crawler %s ;' % company)
    #        except Exception as e:
                logger.debug('crawler error %s; %s' % (company, e))
    #except Exception as e:
        logger.debug('google error %s' % e)
    logger.debug('crawler end')
    try:
#        send_email(games_to_insert, games_to_update, logger, Totle)
        logger.debug('success send email')
    except Exception as e:
        logger.debug('error send email; %s' % e)
    try:
 #       update_data(games_to_insert, games_to_update, logger, db_host, db_user,
 #               db_pass, db_data, db_port)
        logger.debug('insert %d games; update %d games' % (len(games_to_insert), len(games_to_update)))
    except Exception as e:
        logger.debug('error update data; %s' % e)
#    try:
#        crawler_infos = get_crawler_gamename(games_to_insert, logger) 
#        logger.debug("get gamename for google_gamename_mapping success")
#    except Exception as e:
#        logger.debug("get gamename for google_gamename_mapping error: %s" % e)
#    try:
#        insert_google_gamename_mapping(crawler_infos)
#        logger.debug("insert into google_gamename_mapping success")
#    except Exception as e:
#        logger.debug("insert into google_gamename_mapping error: %s" % e)
    logger.debug('Total games %d' % len(Totle))
    logger.debug('Total insert %d' % len(games_to_insert))
    logger.debug('Total update %d' % len(games_to_update))
    logger.debug('End')
    logger.debug('\n')


def get_crawler_gamename(games_to_insert, logger):
    crawler_infos = []
    gamename_mapping = get_mapping_gamename()
    logger.debug("has %d pkgs in mapping" % len(gamename_mapping))
    for key in games_to_insert:
        key_info = key.split('<>')
        area = key_info[0]
        company = key_info[1]
        pkg_name = key_info[2]
        if pkg_name not in gamename_mapping:
            api = login(logger)
            info = get_info(api, pkg_name, logger)
            info = api.toDict(info)
            info = str(info)
            info = info.replace("true", "True")
            info = info.replace("false", "False")
            info = eval(str(info))
            doc = info["docV2"]
            game_name = doc["title"]
            gama_name = ftoj(game_name)
            gamename_mapping[pkg_name] = game_name
            info = {
                    "game_name": game_name,
                    "pkg_name": pkg_name
                }
            crawler_infos.append(info)
    logger.debug("should insert %s pkg in mapping" % len(crawler_infos))
    return crawler_infos


def get_mapping_gamename():
    gamename_mapping = {}
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
        SELECT game_name, pkg_name FROM google_gamename_mapping
            """
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
        for row in cursor.fetchall():
            game_name = row[0]
            pkg_name = row[1]
            gamename_mapping[pkg_name] = game_name
        cursor.close()
        conn.commit()
        conn.close()
    return gamename_mapping


def get_ggzs_gamename():
    ggzs_infos = []
    gamename_mapping = get_mapping_gamename()
    print "has %d pkgs in mapping" % len(gamename_mapping)
    section = "ggzs"
    db_host = cf.get(section, "db_host")
    db_port = cf.getint(section, "db_port")
    db_user = cf.get(section, "db_user")
    db_pass = cf.get(section, "db_pass")
    db_data = cf.get(section, "db_data")
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass,
            port=db_port, db=db_data, charset='utf8')
    cursor = conn.cursor()
    try: 
        sql = """
        SELECT game_name, pkg_name FROM iplay_game_pkg_info WHERE source=3 
            AND (market_channel="GG官方" OR market_channel="Google官方版")
            """
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
        for row in cursor.fetchall():
            game_name = row[0]
            pkg_name = row[1]
            if pkg_name == "com.gameloft.android.ANMP.GloftHOHM":
                game_name = "溷沌与秩序：英雄"
            info = {
                    "game_name": game_name,
                    "pkg_name": pkg_name
                }
            if pkg_name not in gamename_mapping:
                ggzs_infos.append(info)
                gamename_mapping[pkg_name] = game_name
        cursor.close()
        conn.commit()
        conn.close()
    return ggzs_infos


def get_google_gamename():
    google_infos = []
    gamename_mapping = get_mapping_gamename()
    print "has %d pkgs in mapping" % len(gamename_mapping)
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
        SELECT game_name_from_google_api, pkg_name FROM googleplay_games
            """
        cursor.execute(sql)
    except Exception as e:
        conn.rollback()
    finally:
        for row in cursor.fetchall():
            game_name = row[0]
            pkg_name = row[1]
            info = {
                    "game_name": game_name,
                    "pkg_name": pkg_name
                }
            if pkg_name not in gamename_mapping:
                google_infos.append(info)
                gamename_mapping[pkg_name] = game_name
        cursor.close()
        conn.commit()
        conn.close()
    return google_infos


def insert_google_gamename_mapping(infos):
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
        INSERT INTO google_gamename_mapping(
                pkg_name,
                game_name
                ) VALUES(
                %(pkg_name)s
                , %(game_name)s
                )
            """
        cursor.executemany(sql, infos)
    except Exception as e:
        conn.rollback()
        print e
    finally:
        cursor.close()
        conn.commit()
        conn.close()


def backup_gamename():
    ggzs_infos = get_ggzs_gamename()
    print "insert %s data from ggzs" % len(ggzs_infos)
    insert_google_gamename_mapping(ggzs_infos)
    google_infos = get_google_gamename()
    print "insert %s data from google" % len(google_infos)
    insert_google_gamename_mapping(google_infos)


if __name__=='__main__':
    '''
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # 创建handler，用于写入文件
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    LOGS_DIR = os.path.join(BASE_DIR, 'log\\360_minutes_%s.log' % get_date())
    LOGS_DIR = '360_minutes.log'
    #LOGS_DIR = 'log\\360_minutes_%s.log' % get_date()
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
    area = 'ceshi'
    company = '123'

    key1 = '%s<>%s<>%s' % (area, company, 'Overkill')
    key2 = '%s<>%s<>%s' % (area, company, 'bbb')
    games_to_insert = {key1:{'update_time':
        233,'game_name':'test1','file_size':2323}}
    games_to_update = {key2:{'update_time':
        23323,'game_name':'时空水晶','file_size':2323}}
    Totle = {key1:{'update_time':
        23323,'game_name':'时空水晶','file_size':2323}}
 
    #key = '%s<>%s<>%s' % (area, company, pkg_name)
    send_email(games_to_insert, games_to_update, logger, Totle)
    '''

#    backup_gamename()
    job()
#    schedule.every(10).minutes.do(job)
#    while True:
#        schedule.run_pending()
#        time.sleep(1)

