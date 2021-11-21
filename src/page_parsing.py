import random
from bs4 import BeautifulSoup
import requests
import time
import pymongo
import json

header1 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.53',
    'Cookie': 'UOR=cloud.tencent.com,service.weibo.com,cloud.tencent.com; SINAGLOBAL=2396057328931.58.1636889247855; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWrCEIbWDZTAd_wSdM5aVAh5JpX5KMhUgL.FoM01hBNShef1hB2dJLoIpnLxKqLBK.L1KnLxK-LBKBL12qEehz7ehzt; SCF=ApLMvs3csWvjZwfYsx3q-yLGg4FFSIsKjpGJegzXO4RvKAQ3SpzQ7tOsP3clqaEJrjXqOHNYVnW0gPapV16QDsQ.; SUB=_2A25MkXfhDeRhGeFN41YW9C3JwziIHXVv5-4prDV8PUNbmtB-LUTskW9NQ90uMpb5B8jMpo0Gp-H7DwxxEH8nQDOo; ALF=1668692784; SSOLoginState=1637156785; _s_tentry=weibo.com; Apache=3731130940706.864.1637157336131; ULV=1637157336237:4:4:4:3731130940706.864.1637157336131:1637081410405'
}
header2 = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/95.0.4638.69',
    'Cookie': 'UOR=cloud.tencent.com,service.weibo.com,cloud.tencent.com; SINAGLOBAL=2396057328931.58.1636889247855; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWrCEIbWDZTAd_wSdM5aVAh5JpX5KMhUgL.FoM01hBNShef1hB2dJLoIpnLxKqLBK.L1KnLxK-LBKBL12qEehz7ehzt; SCF=ApLMvs3csWvjZwfYsx3q-yLGg4FFSIsKjpGJegzXO4RvKAQ3SpzQ7tOsP3clqaEJrjXqOHNYVnW0gPapV16QDsQ.; SUB=_2A25MkXfhDeRhGeFN41YW9C3JwziIHXVv5-4prDV8PUNbmtB-LUTskW9NQ90uMpb5B8jMpo0Gp-H7DwxxEH8nQDOo; ALF=1668692784; SSOLoginState=1637156785; _s_tentry=weibo.com; Apache=3731130940706.864.1637157336131; ULV=1637157336237:4:4:4:3731130940706.864.1637157336131:1637081410405'
}
client = pymongo.MongoClient('localhost', 27017)
epidemic_data = client['epidemic_data']
final_data = epidemic_data['business_intelligence']
base_url = 'https://m.weibo.cn/detail/'
start_url = 'https://s.weibo.com/weibo/%25E7%2596%25AB%25E6%2583%2585?q=%E7%96%AB%E6%83%85&typeall=1&suball=1&timescope=custom:'


# 爬取微博详情界面内容和评论
# 发微博时间有指向详细页面的链接
# m.weibo.cn直接用https://m.weibo.cn/status/KFkJXmwB7为例，”KFkJXmwB7“是微博的唯一标识符
# 评论在https://m.weibo.cn/statuses/show?id=KFkJXmwB7
def get_data_from(url, page, date):
    true_url = url + str(page)
    wb_data = requests.get(true_url, headers=header1)
    time.sleep(random.randint(0, 3))
    Soup = BeautifulSoup(wb_data.text, 'lxml')
    # detail_urls = Soup.select('#pl_feedlist_index > div:nth-child(2) > div')
    detail_urls = Soup.select('#pl_feedlist_index > div:nth-child(2) > div > div > div.card-feed > '
                              'div.content > p.from > a:nth-child(1)')
    if len(detail_urls) == 0:
        print(date + '第' + str(page) + '页,' + '无效地址,不能爬取')
        return
    itemNum = 0
    for detail_url in detail_urls:
        # 转换为移动端网址爬取数据
        # 获取唯一标识符
        itemNum = itemNum + 1
        detail = detail_url.get('href')
        bid = getBid(detail)
        print('可以爬取' + date + '第' + str(page) + '页' + '第' + str(itemNum) + '项')
        get_data_from_detail_url(bid, date)


# 进入详细页爬取
def get_data_from_detail_url(id, date):
    try:
        content_url = 'https://m.weibo.cn/statuses/show?id=' + id
        content_data = requests.get(content_url, headers=header2)
        time.sleep(random.randint(0, 3))
        text = json.loads(content_data.text)
        content = text['data']['text'].replace('<br />', '')
        reposts_count = text['data']['reposts_count']
        comments_count = text['data']['comments_count']
        attitudes_count = text['data']['attitudes_count']
        mid = text['data']['mid']
        # print(content)
        comment_url = 'https://m.weibo.cn/comments/hotflow?id=' + mid + '&mid=' + mid + '&max_id_type=0'
        comment_data = requests.get(comment_url, headers=header2)
        list = []
        if comments_count != 0 and comments_count != 1:
            comments = json.loads(comment_data.text)['data']['data']
            for comment in comments:
                list.append(deleteByStartAndEnd(comment['text'], '<', '>'))
                subComment = comment['comments']
                if subComment != False:
                    for item in subComment:
                        list.append(deleteByStartAndEnd(item['text'], '<', '>'))
        data = {
            'url': 'https://m.weibo.cn/detail/' + id,
            'date': date,
            'content': deleteByStartAndEnd(content, '<', '>'),
            'reposts_count': reposts_count,
            'comments_count': comments_count,
            'attitudes_count': attitudes_count,
            'comments': list,
        }
        final_data.insert_one(data)
        print('成功')
    except:
        print("错误")


def deleteByStartAndEnd(s, start, end):
    while '<' in s:
        # 找出两个字符串在原始字符串中的位置，开始位置是：开始始字符串的最左边第一个位置，结束位置是：结束字符串的最右边的第一个位置
        x1 = s.index(start)
        x2 = s.index(end) + len(end)  # s.index()函数算出来的是字符串的最左边的第一个位置
        # 找出两个字符串之间的内容
        x3 = s[x1:x2]
        # 将内容替换为控制符串
        s = s.replace(x3, "")
    return s


def getBid(detail_url):
    detail_url = detail_url.strip('//')
    a = detail_url.split('?', 1)[0]
    bid = a.split('/', )[2]
    return bid


if __name__ == '__main__':
    list1 = []
    # for i in range(1, 30):
    #     list1.append('2019-12-' + str(i))
    for i in range(20, 30):
        list1.append('2020-1-' + str(i))
    for i in range(2, 12):
        for k in range(1, 30):
            list1.append('2020-' + str(i) + '-' + str(k))
    for i in range(1, 10):
        for k in range(1, 30):
            list1.append('2021-' + str(i) + '-' + str(k))
    for item in list1:
        for i in range(0, 2):
            j = random.randint(1, 49)
            get_data_from(start_url + item + ':' + item + '&Refer=g&page=', j, item)
# get_data_from('https://s.weibo.com/weibo?q=%E7%96%AB%E6%83%85&typeall=1&suball=1&timescope=custom:2019-12-17:2019-12-17&Refer=g&page=',1,'2019-12-17')
