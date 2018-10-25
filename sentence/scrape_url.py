# -*- coding: utf-8 -*-
#encoding=utf-8

import requests
import time

import csv
import json
import lxml.html
#import HTMLParser
import datetime

import traceback
import logging

import os
import sys
from urllib import unquote
import re

########

PARAMETERS = {
    'url':'http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord+1+AJLX++%E6%A1%88%E4%BB%B6%E7%B1%BB%E5%9E%8B:%E5%88%91%E4%BA%8B%E6%A1%88%E4%BB%B6&conditions=searchWord+%E6%96%B0%E7%96%86%E7%BB%B4%E5%90%BE%E5%B0%94%E8%87%AA%E6%B2%BB%E5%8C%BA+++%E6%B3%95%E9%99%A2%E5%9C%B0%E5%9F%9F:%E6%96%B0%E7%96%86%E7%BB%B4%E5%90%BE%E5%B0%94%E8%87%AA%E6%B2%BB%E5%8C%BA',
    #'date_range':['2012-01-01','2012-12-31', 1],
}

proxies = {
  "http": "http://sg.proxymesh.com:31280",
  "https": "http://sg.proxymesh.com:31280",
}
proxies = None ## comment out this line to enable proxies.

########

DOWNLOAD_DELAY = 0.1

def delay_reset():
    global DOWNLOAD_DELAY
    DOWNLOAD_DELAY = 0.1
    #print 'Sleeping value reset'

def delay_show():
    global DOWNLOAD_DELAY
    print 'Sleeping value:', DOWNLOAD_DELAY

def delay_add():
    global DOWNLOAD_DELAY
    if DOWNLOAD_DELAY<1:
        DOWNLOAD_DELAY = 3
    else:
        DOWNLOAD_DELAY *= 2
    if DOWNLOAD_DELAY>600:
        DOWNLOAD_DELAY = 600

def delay():
    global DOWNLOAD_DELAY
    print 'Sleeping', DOWNLOAD_DELAY
    time.sleep(DOWNLOAD_DELAY)

def myip():
    r = requests.get('http://www.ip138.com', proxies=proxies)
    if not '<iframe src="' in r.text:
        print 'API not found!'
        return
    #url = 'http://1111.ip138.com/ic.asp'
    url = r.text.split('<iframe src="',1)[1].split('"',1)[0]
    r = requests.get(url, proxies=proxies)
    tmp = re.findall(r'\[.+\]', r.text)
    if tmp:
        print 'Your IP in internet is', tmp[0]
    else:
        print 'API Error!'

def main():

    #with open('keys.json','rb') as f:
    #    data = f.read()

    #keys = json.loads(data)

    #print keys[3]['Child'][0]['Key']

    #print u'案件类型:刑事案件,裁判日期:2016-03-02  TO  2016-03-02,法院地域:浙江省'
    #print u'案件类型:刑事案件,裁判日期:%s  TO  %s,法院地域:%s' % ('2016-03-02', '2016-03-02', keys[3]['Child'][0]['Key'])

    argv = sys.argv
    if len(argv)>1:
        PARAMETERS['url'] = argv[1]
    if len(argv)>2:
        ss = argv[2].split(',')
        if len(ss)<=2:
            ss.append(10000)
        else:
            ss[2] = int(ss[2])
        PARAMETERS['date_range'] = ss

    url = PARAMETERS.get('url')

    logging.basicConfig(filename='logging.txt', format="%(asctime)s;%(levelname)s;%(message)s", level=logging.INFO)

    ss = [s.split('&')[0].replace('+','') for s in url.split('++')[1:]]
    #ss = [unquote(s).decode('utf-8') for s in ss]
    ss = [unquote(s) for s in ss]

    f = open('logging.csv','ab')
    writer = csv.writer(f)

    session = getASession()

    print 'Proxies:', proxies
    myip()

    scrape(writer, ss, session)

    f.close()

def getASession():

    return requests.Session()

def scrape(writer, searchs, session):

    print 'parameters:', searchs

    #dr = PARAMETERS.get('date_range')
    #if dr:
    #    for retry_time in range(5):
    #        try:
    #            scrape_date(writer, searchs, dr[0], dr[1], session)
    #            break
    #        except Exception, e:
    #            print e
    #            traceback.print_exc()
    #            logging.exception("Scraping %s" % date1.strftime('%Y-%m-%d'))
    #            logging.exception("%s" % e)
    #
    #            print 'retry_time:', retry_time+1
    #            if retry_time>=5:
    #                print '!!! Give up scraping ', date1.strftime('%Y-%m-%d')
    #            else:
    #                print '!!! Retry scraping ', date1.strftime('%Y-%m-%d')
    #            try:
    #                session = getASession()
    #            except Exception, e:
    #                print e
    #                traceback.print_exc()
    #                logging.exception("%s" % e)
    #    return

    formdata = {
        #'Param':u'案件类型:刑事案件,裁判日期:%s  TO  %s'  % (key_date1, key_date2),
        'Param':','.join(searchs),
    }

    #r = session.post('http://wenshu.court.gov.cn/List/TreeContent',
    #    data=formdata, headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'})
    r = requests.post('http://wenshu.court.gov.cn/List/TreeContent',
        data=formdata, headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'}, proxies=proxies)

    #print 'r.text:', r.text[:1000]
    #return
    #data = r.text[1:-1].replace('\\"','"')
    data = r.text[1:-1].replace('\\\\','\\').replace('\\"','"')
    keys = json.loads(data)
    #print keys[4]['Child'][0]['Key']
    #print keys[4]['Child']
    years = []
    #print 'TreeContent'
    for d in keys[4]['Child']:
        print '--', d['Key'], d['IntValue']
        if d['IntValue']!=0:
            years.append([d['Key'], d['IntValue']])
    print 'years:', len(years)
    #with open('keys.json','w') as f:
    #    f.write(json.dumps(keys))
    dates = []
    for year, count in years:
        #print year, count
        dt_start = datetime.date(int(year),1,1)
        dt_end = datetime.date(int(year),12,31)
        if count>=500:
            dt = dt_start
            while dt <= dt_end:
                dates.append([dt.strftime('%Y-%m-%d'), dt.strftime('%Y-%m-%d')])
                dt = dt + datetime.timedelta(1)
        else:
            dates.append([dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')])
    dr = PARAMETERS.get('date_range')
    if dr:
        dates = []
        ss = dr[0].split('-')
        dt_start = datetime.date(int(ss[0]),int(ss[1]),int(ss[2]))
        ss = dr[1].split('-')
        dt_end = datetime.date(int(ss[0]),int(ss[1]),int(ss[2]))
        if dr[2]>=500:
            dt = dt_start
            while dt <= dt_end:
                dates.append([dt.strftime('%Y-%m-%d'), dt.strftime('%Y-%m-%d')])
                dt = dt + datetime.timedelta(1)
        else:
            dates.append([dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')])
    print 'Date range count:', len(dates)
    #return
    #retry_time = 0
    for date1, date2 in dates: ###
        for retry_time in range(5):
            try:
                delay_show()
                scrape_date(writer, searchs, date1, date2, session)
                break
            except Exception, e:
                print e
                traceback.print_exc()
                logging.exception("Scraping %s to %s" % (date1, date2))
                logging.exception("%s" % e)
                delay_add()
                delay()

                print 'retry_time:', retry_time+1
                if retry_time>=5:
                    print '!!! Give up scraping ', date1, date2
                else:
                    print '!!! Retry scraping ', date1, date2
                try:
                    session = getASession()
                except Exception, e:
                    print e
                    traceback.print_exc()
                    logging.exception("%s" % e)


def scrape_date(writer, searchs, key_date1, key_date2, session):

    print 'parameters:', key_date1, key_date2, searchs
    s_date = u'裁判日期:%s  TO  %s'  % (key_date1, key_date2)

    formdata = {
        #'Param':u'案件类型:刑事案件,裁判日期:%s  TO  %s'  % (key_date1, key_date2),
        'Param':','.join(searchs+[s_date.encode('utf-8')]),
    }

    #r = session.post('http://wenshu.court.gov.cn/List/TreeContent',
    #    data=formdata, headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'})
    r = requests.post('http://wenshu.court.gov.cn/List/TreeContent',
        data=formdata, headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'}, proxies=proxies)

    #print 'r.text:', r.text[:1000]
    #return
    #data = r.text[1:-1].replace('\\"','"')
    data = r.text[1:-1].replace('\\\\','\\').replace('\\"','"')
    keys = json.loads(data)
    #print keys[4]['Child'][0]['Key']
    #print keys[4]['Child']
    branches = []
    #print 'TreeContent'
    for d in keys[3]['Child']:
        print '--', d['Key'], d['IntValue']
        if d['IntValue']!=0:
            branches.append([d['Key'], d['IntValue']])
    print 'branches:', len(branches)

    formdata = {
        'Param':u'案件类型:刑事案件,裁判日期:2016-03-02  TO  2016-03-02,法院地域:浙江省',
        'Index':'1',
        'Page':'20',
        'Order':u'法院层级',
        'Direction':'asc'
    }

    #formdata['Param'] = u'案件类型:刑事案件,裁判日期:%s  TO  %s,法院地域:%s' % (key_date, key_date, u'浙江省')
    b_searchs = [s for s in searchs if not u'法院地域'.encode('utf-8') in s]
    #print b_searchs
    #print searchs
    #return
    for branch in branches: ###
        s_branch = u'法院地域:%s'  % branch[0]
        pages = (branch[1]-1)/20+1
        for page in range(pages): ###
            # Crawl a page
            retry_time = 0
            #fail = True
            while retry_time<3:
                #fail = False
                retry_time += 1
                try:
                    #formdata['Param'] = u'案件类型:刑事案件,裁判日期:%s  TO  %s,法院地域:%s' % (key_date1, key_date2, branch[0])
                    formdata['Param'] = ','.join(b_searchs+[s_branch.encode('utf-8'), s_date.encode('utf-8')]),
                    formdata['Index'] = str(page+1)

                    #r = session.post('http://wenshu.court.gov.cn/List/ListContent',
                    #    data=formdata, headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'})
                    r = requests.post('http://wenshu.court.gov.cn/List/ListContent',
                        data=formdata, headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'}, proxies=proxies)
                    time.sleep(1)

                    #print 'r.text:', r.text[:100]
                    #return
                    data = r.text[1:-1].replace('\\\\','\\').replace('\\"','"')
                    j = json.loads(data)
                    #print 'Count:', j[0]['Count']
                    #print j[1][u'文书ID']
                    # print j[1][u'DocContent']
                    if len(j)<2:
                        continue
                    print 'Scraping:', key_date1, key_date2, branch[0], branch[1], page+1
                    writer.writerow([key_date1, key_date2, branch[0].encode('utf-8'), branch[1], page+1])
                    for row in j[1:]: ###
                        #print 'row:', row
                        retry_doc = 0
                        if os.path.exists('text/%s.txt' % row[u'文书ID']):
                            print 'existing ', row[u'文书ID']
                            continue
                        tmp = row.get(u'DocContent')
                        #print h.unescape(h.unescape(tmp))
                        if tmp:
                            print 'Writing ', row[u'文书ID']
                            with open('text/%s.txt' % row[u'文书ID'],'wb') as f:
                                f.write(h.unescape(h.unescape(tmp)).encode('utf-8'))
                        #else:
                        #    print '!!! No DocContent.'
                        # GET http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=46d4459c-6328-48b9-908a-65626c3bfdd3
                        else:
                            #r = session.get('http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=%s' % row[u'文书ID'])
                            retry_doc = 0
                            while retry_doc<3:
                                retry_doc += 1
                                try:
                                    r = requests.get('http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=%s' % row[u'文书ID'], proxies=proxies)
                                    data = r.text.split('jsonHtmlData = "',1)[1].split('";',1)[0].replace('\\\\','\\').replace('\\"','"')
                                    j = json.loads(data)
                                    html = '<html><head><meta charset="utf-8"></head><body>'+os.linesep
                                    html += j.get('Title','').encode('utf-8')+'<br>'
                                    html += u'发布日期：'.encode('utf-8')+j.get('PubDate','').encode('utf-8')+'<br>'
                                    tmp = j.get('Html','')
                                    html += tmp.encode('utf-8')
                                    html += '</body></html>'+os.linesep
                                    print 'Writing ', row[u'文书ID']
                                    with open('html/%s.html' % row[u'文书ID'],'wb') as f:
                                        f.write(html)
                                    with open('text/%s.txt' % row[u'文书ID'],'wb') as f:
                                        text = html
                                        try:
                                            text = lxml.html.fromstring(html.replace('<br>', os.linesep).replace('<br/>', os.linesep).strip()).text_content().strip().encode('utf-8')
                                        except Exception, e:
                                            print e
                                            traceback.print_exc()
                                        f.write(text)
                                    break

                                except Exception, e:
                                    delay()
                                    print 'Document retry time:', retry_doc

                        if retry_doc==0:
                            delay_reset()
                    retry_time += 100
                    delay_reset()

                except Exception, e:
                    delay_add()
                    delay()
                    print e
                    traceback.print_exc()
                    logging.exception("Scraping page error." + key_date1)
                    logging.exception("%s" % e)

                    print 'page retry_time:', retry_time
                    if retry_time>=3:
                        print '!!! Give up scraping page' + key_date1
                        break
                    try:
                        session = getASession()
                    except Exception, e:
                        print e
                        traceback.print_exc()
                        logging.exception("%s" % e)


if __name__ == '__main__':
    main()
