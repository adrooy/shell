#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
reload(sys)
sys.setdefaultencoding("utf-8")



#fromaddr = 'backend_robot@lbesec.com'
toaddr = ["sunzhennan@lbesec.com", "gaoruowei@lbesec.com",
       "cuizhanzhe@lbesec.com", "sangyu@lbesec.com", "wangxin@lbesec.com", "liupeidong@lbesec.com",
       "liyang@lbesec.com", "anyangyang@lbesec.com", "wangchanghai@lbesec.com",
       "liwei@lbesec.com", "kangkaikai@lbesec.com", "xiangxiaowei@lbesec.com"]
ccaddr = []
#ccaddr = ['limingdong@lbesec.com', 'sunzhennan@lbesec.com', 'xiangxiaowei@lbesec.com', 'zhaoqing@lbesec.com', 'duchunhai@lbesec.com', 'liushaokai@lbesec.com']
#toaddr = ["xiangxiaowei@lbesec.com","sunzhennan@lbesec.com","sangyu@lbesec.com","wangxin@lbesec.com"]
#ccaddr = ["53949131@qq.com", "sunzhennan@lbesec.com"]
#toaddr = ['xiangxiaowei@lbesec.com']
#ccaddr = ['xiangxiaowei@lbesec.com']
#smtp默认端口为25，如果stmp开启了ssl,就需要 465（SSL）和 587（TLS）
#sinaServer = '192.168.1.66'
#username = 'backend_robot'
#password = 'MhyTtBqtq'
sinaServer = 'smtp.163.com'
username = 'adrlbe@163.com'
password = '215481379'
fromaddr = 'adrlbe@163.com'


def send_email(from_addr, to_addr_list, cc_addr_list,
               subject, message,
               login, password,
               smtpserver):
    # header = 'From: %s\n' % from_addr
    # header += 'To: %s\n' % ','.join(to_addr_list)
    # header += 'Cc: %s\n' % ','.join(cc_addr_list)
    # header += 'Subject: %s\n\n' % subject
    # message = header + message
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ','.join(to_addr_list)
    msg['Cc'] = ','.join(cc_addr_list)
    msg['Subject'] = subject

    #Next, we attach the body of the email to the MIME message:
    msg.attach(MIMEText(message, 'html'))

    server = smtplib.SMTP(smtpserver)
    # server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(login, password)
    problems = server.sendmail(from_addr, to_addr_list, msg.as_string())
    if problems:
        print problems
    server.quit()


def send(subject, message):
    send_email(from_addr=fromaddr,
               to_addr_list=toaddr,
               cc_addr_list=ccaddr,
               subject=subject,
               message=message,
               login=username,
               password=password,
               smtpserver=sinaServer)


if __name__ == '__main__':
    send('test email', 'msg....')
    print "EOF"
