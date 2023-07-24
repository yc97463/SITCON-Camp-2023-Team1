import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import random
import urllib.request

def get_random_subpage(base_url, url):
    response = requests.get(url)

    # 檢查是否成功獲取網頁內容
    if response.status_code == 200:
    # 使用BeautifulSoup解析網頁內容
        soup = BeautifulSoup(response.text, 'html.parser')
        linkstitle = soup.find_all('div', class_='post-title')
        activitylinks = []
        for links in linkstitle:
            a = links.find('a')['href']
            activitylinks.append(a)
    
    return random.choice(activitylinks)

        
def scrap_subpages_data(url):

    # 使用requests套件獲取網頁內容
    response = requests.get(url)

    # 檢查是否成功獲取網頁內容
    if response.status_code == 200:
        # 使用BeautifulSoup解析網頁內容
        soup = BeautifulSoup(response.text, 'html.parser')
    
        # 找到活動資訊所在的HTML元素
        activity_info = soup.find('ul', class_='list list-lines')
        aaa = activity_info.find_all('li')

        activity_data = {
        'title': soup.find('div', class_='post-title').text.replace('\n', ''),
        'date': (aaa[0].text[6:16]),
        'prize': None,
        'exp': None,
        'min_age': 0,
        'max_age':999,
        'category':'其他',
        'url': (aaa[3].text[6:]),
        }
    return (activity_data)
    
# 自行定義目標網站的 URL
base_url = 'https://skyline.tw/activity/explore?'

def crawl_skyline():
    # 獲取隨機子網站的 URL
    random_subpage_url = get_random_subpage(base_url, base_url)
    data = scrap_subpages_data(random_subpage_url)
    return data