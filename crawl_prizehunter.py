import requests
import json
import datetime
from typing import Union, Dict, List
import re
import random

def crawl_prizehunter():

    result = {}
    def my_parse(obj:Union[dict, list], result):

        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in ('identifyLimit','title','tags','prizeTop','endTime','officialUrl','categories'):
                    result[key] = val
                if isinstance(val, dict):
                    my_parse(val, result)
                elif isinstance(val, list): 
                    my_parse(val, result)
                    
        elif isinstance(obj, list):
            for ele in obj:
                my_parse(ele, result)
                
    # scraping
    url_list = [
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/ez8lts1r8j4r9smp47?language=tw',
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/1n873k3ypo0alssce5?language=tw',
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/CFI2023?language=tw',
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/67s8vb4huot5vkp23o?language=tw',
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/utobevm03syk6bjj2g?language=tw',
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/v71rnww9z8vr69kevf?language=tw',
        'https://api.bhuntr.com/tw/cms/bhuntr/contest/vut1yt42rp1n2kfcmz?language=tw'
    ]
    url = random.choice(url_list)
    res = requests.get(url)
    data = res.json()

    # print(type(data), end="\n\n")
    # print(data, end="\n\n")

    my_parse(data, result)

    # 把title移到 dic 的最前面(這裡可以簡化但到時候再說)
    title_value = result['title']
    del result['title']
    title_dic = {}
    title_dic['title'] = title_value
    title_dic.update(result)

    # 把 unix time 改為西元時間
    endTime_value = title_dic['endTime']
    title_dic["endTime"] = datetime.datetime.fromtimestamp(endTime_value)
    title_dic['endTime'] = title_dic['endTime'].strftime('%Y-%m-%d')

    # 設定年齡
    title_dic['min_age'] = 0
    title_dic['max_age'] = 999

    # print("raw tags: ", title_dic['tags'])
    # 設定分類: 把 tags 統整並分為 {資訊、語文、生物、設計、攝影 其他}
    for tag in title_dic['tags']:
        if tag in ['資訊', '語文', '生物', '設計', '繪畫','音樂','體育'] or (re.search('攝影.*', tag)) != None:
            title_dic['category'] = tag
            break
        else:
            title_dic['category'] = '其他'

    for cat in title_dic['categories']:
        if cat in ['111','112']:
            title_dic['category'] = '攝影'
        elif cat in ['107']:
            title_dic['category'] = '繪畫'
        elif cat in ['108','109','110']:
            title_dic['category'] = '設計'
        elif cat in ['114','115']:
            title_dic['category'] = '語文'
        elif cat in ['119','120','121']:
            title_dic['category'] = '音樂'
        elif cat in ['143']:
            title_dic['category'] = '體育'

    del title_dic['tags']
    del title_dic['categories']

    # 改key的名字(+排各條件順序)
    title_dic['date'] = title_dic.pop('endTime')
    title_dic['prize'] = title_dic.pop('prizeTop')
    title_dic['url'] = title_dic.pop('officialUrl')

    # 整理 exp
    # 把 none&other 先從dic刪掉 (因為這樣後面比較好寫)
    del title_dic['identifyLimit']['none']
    del title_dic['identifyLimit']['other']
    for key in title_dic['identifyLimit']:
        if title_dic['identifyLimit'][key] == True:
            if key == 'nonStudent':
                title_dic['exp'] = '社會人士'
            elif key == 'University':
                title_dic['exp'] = '學士'
            elif key == 'highSchool':
                title_dic['exp'] = '高中職'
            elif key == 'juniorHighSchool':
                title_dic['exp'] = '國中'
            elif key == 'primarySchool':
                title_dic['exp'] = '國小'
        else:
            title_dic['exp'] = None

    del title_dic['identifyLimit']

    # 回傳整理後資料庫
    return (title_dic)