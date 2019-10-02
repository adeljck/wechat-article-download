#!/usr/bin/python3
# coding:utf-8
import sys
import time
import json
import random
import requests
import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import config


def get_wechat_cookies():
    cookies = {}
    broser = webdriver.Chrome()
    # broser.implicitly_wait(5)
    broser.maximize_window()
    broser.get('https://mp.weixin.qq.com/')
    broser.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[1]/div[1]/div/span/input').send_keys(
        config.WECHAT_ACCOUNT)
    broser.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[1]/div[2]/div/span/input').send_keys(
        config.WECHAT_ACCOUNT_PASSWORD)
    broser.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[3]/label/i').click()
    broser.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[4]/a').click()
    try:
        WebDriverWait(broser, 20).until(
            EC.text_to_be_present_in_element((By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[1]/h3'), u"帐号整体情况"))
    except:
        broser.close()
        print('就不能乖乖扫个码？')
        sys.exit(0)
    cookie_items = broser.get_cookies()
    token = broser.current_url.split('=')[-1]
    broser.close()
    for cookie_item in cookie_items:
        cookies[cookie_item['name']] = cookie_item['value']
    return {"cookies": cookies, "token": token}


def get_fakeid(token, query, cookies):
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
    parma = {
        "action": "search_biz",
        "token": token,
        "lang": "zh_CN",
        'f': 'json',
        "ajax": 1,
        "random": random.random(),
        "query": query,
        "begin": 0,
        "count": 5
    }
    re = requests.get(search_url, cookies=cookies, params=parma, headers=config.HEADERS)
    search_result = json.loads(re.text)
    if search_result['total'] == 0:
        print("找不到相关公众号")
    if search_result['total'] > 1:
        fakeid = select_account(search_result['total'])
        return fakeid
    if search_result['total'] == 1:
        fakeid = search_result['list'][0]['fakeid']
        return fakeid


def select_account(total):
    if total % 5 != 0:
        import math
        page = math.floor(total / 5) + 1
    else:
        page = total / 5
    for i in range(0, page + 1):
        pass


def get_doc_info(fake_id, cookies, token):
    infos = []
    conn = pymysql.connect(
        host=config.HOST,
        port=config.PORT,
        user=config.USERNAME,
        password=config.PASSWORD,
        charset=config.CHARSET,
        db=config.DB
    )
    cur = conn.cursor()
    result_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg'
    parmare = {
        "action": "list_ex",
        "token": token,
        "lang": "zh_CN",
        'f': 'json',
        "ajax": 1,
        "random": random.random(),
        "query": "",
        "begin": 0,
        "count": 5,
        "fakeid": fake_id,
        "type": 9
    }
    re = requests.get(result_url, cookies=cookies, params=parmare, headers=config.HEADERS)
    total = json.loads(re.text)['app_msg_cnt']
    if total % 5 != 0:
        import math
        page = math.floor(total / 5) + 1
    else:
        page = total / 5
    interep = int(input("共{}页，{}篇文章,搞几页:".format(page, total))) - 1
    for begin in range(0, interep * 5 + 1, 5):
        time.sleep(5)
        parmare["begin"] = begin
        re = requests.get(result_url, cookies=cookies, params=parmare, headers=config.HEADERS)
        datas = json.loads(re.text)['app_msg_list']
        for data in datas:
            if not cur.execute('select * from wechat where aid="{}"'.format(data['aid'])):
                infos.append(data)
    return infos


def is_exitst(info):
    conn = pymysql.connect(
        host=config.HOST,
        port=config.PORT,
        user=config.USERNAME,
        password=config.PASSWORD,
        charset=config.CHARSET,
        db=config.DB
    )
    cur = conn.cursor()
    sql = 'select * from wechat where aid="{}"'.format(info)
    if not cur.execute(sql):
        return 1


def parse_info(infos):
    conn = pymysql.connect(
        host=config.HOST,
        port=config.PORT,
        user=config.USERNAME,
        password=config.PASSWORD,
        charset=config.CHARSET,
        db=config.DB
    )
    cur = conn.cursor()
    sql = "insert into wechat(aid,appmsgid,cover,create_time,digest,item_show_type,itemidx,link,title,update_time) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    data_list = []
    for info in infos:
        result = (
            info['aid'], info['appmsgid'], info['cover'], info['create_time'], info['digest'], info['item_show_type'],
            info['itemidx'], info['link'], info['title'],
            info['update_time'])
        data_list.append(result)
    content = cur.executemany(sql, data_list)
    if content:
        print('成功插入{}条数据'.format(len(infos)))
    if not content:
        print('成功插入{}条数据'.format(len(infos)))
    conn.commit()


def main():
    query = input('输入要提取的公众号:')
    datas = get_wechat_cookies()
    fake_id = get_fakeid(datas["token"], query, datas["cookies"])
    if isinstance(fake_id, str):
        infos = get_doc_info(fake_id, datas["cookies"], datas["token"])
        parse_info(infos)
    else:
        for i in fake_id.keys():
            print(i)
            sys.exit(0)


if __name__ == '__main__':
    main()
