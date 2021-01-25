from bs4 import BeautifulSoup
import requests
import time
import pymongo
import json

header1 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
    'Cookie':'SINAGLOBAL=6717687578078.786.1602305484145; login_sid_t=70acb009c278a06379c6a994b372144e; cross_origin_proto=SSL; _s_tentry=passport.weibo.com; Apache=5101764635875.548.1611396125043; ULV=1611396125050:24:2:1:5101764635875.548.1611396125043:1609519425799; SSOLoginState=1611415721; SCF=Au0TNecSqElqfUi2oChYnQs01pHAI6HV5Ypr-Fs99D9gdbNxqvaordY8YfJ0OMtKx73NMbFbFY0hrUlZ_-l844o.; wvr=6; ALF=1614008490; SUB=_2A25NCDP6DeRhGeFN41YW9C3JwziIHXVu812yrDV8PUJbkNAKLVLmkW1NQ90uMiIB6Jn1oJy5KaW7F0iVS-eI0-N3; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWrCEIbWDZTAd_wSdM5aVAh5JpX5oz75NHD95QNe0nXS0B0SKnXWs4Dqcjqi--ci-24iK.Ri--fi-2XiKyseo5Eeh5E; UOR=,,www.baidu.com; wb_timefeed_7384743584=1; wb_view_log_7384743584=1536*8641.25; webim_unReadCount=%7B%22time%22%3A1611536173313%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A8%2C%22msgbox%22%3A0%7D'
}
header2 = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/88.0.4324.96',
    'Cookie':'_T_WM=13370261750; SCF=Au0TNecSqElqfUi2oChYnQs01pHAI6HV5Ypr-Fs99D9gn_YLvnAv6sj_BfsdgIdGY2Z9jlX_IzKuhqRPzW-dj3s.; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWrCEIbWDZTAd_wSdM5aVAh5NHD95QNe0nXS0B0SKnXWs4Dqcjqi--ci-24iK.Ri--fi-2XiKyseo5Eeh5E; SUB=_2A25NCDP5DeRhGeFN41YW9C3JwziIHXVu812xrDV6PUJbkdAKLW7ykW1NQ90uMlNftszhg6p-F5fopgCaaBHDiEi0; SSOLoginState=1611416489; WEIBOCN_FROM=1110103030; XSRF-TOKEN=4bfb23; MLOGIN=1; M_WEIBOCN_PARAMS=fid%3D1076037384743584%26uicode%3D10000011'
}
client = pymongo.MongoClient('localhost', 27017)
epidemic_data = client['epidemic_data']
final_data = epidemic_data['final_data']
base_url = 'https://m.weibo.cn/detail/'
start_url='https://s.weibo.com/weibo/%25E7%2596%25AB%25E6%2583%2585?q=%E7%96%AB%E6%83%85&typeall=1&suball=1&timescope=custom:'


# 爬取微博详情界面内容和评论
def get_data_from(url,page,date):
    true_url = url + str(page)
    wb_data = requests.get(true_url,headers=header1)
    time.sleep(3)
    Soup = BeautifulSoup(wb_data.text, 'lxml')
    detail_url=Soup.select('#pl_feedlist_index > div:nth-child(2) > div')
    if len(detail_url)==0:
        print(date+'第'+str(page)+'页,'+'无效地址,不能爬取')
        return
    for k in detail_url:
        #转换为移动端网址爬取数据
        detail=k.get('mid')
        print('可以爬取'+date+'第'+str(page)+'页')
        get_data_from_detail_url(detail,date)

#进入详细页爬取
def get_data_from_detail_url(id,date):
    try:
        content_url='https://m.weibo.cn/statuses/extend?id='+id
        comment_url='https://m.weibo.cn/comments/hotflow?id='+id+'&mid='+id+'&max_id_type=0'
        content_data=requests.get(content_url,headers=header2)
        time.sleep(3)
        text = json.loads(content_data.text)
        content=text['data']['longTextContent'].replace('<br />','')
        reposts_count=text['data']['reposts_count']
        comments_count=text['data']['comments_count']
        attitudes_count=text['data']['attitudes_count']
        #print(content)
        comment_data=requests.get(comment_url,headers=header2)
        time.sleep(3)
        list=[]
        if comments_count!=0 and comments_count!=1:
            comments=json.loads(comment_data.text)['data']['data']
            for comment in comments:
                list.append(deleteByStartAndEnd(comment['text'],'<','>'))
        data={
            'url':'https://m.weibo.cn/detail/'+id,
            'date':date,
            'content':deleteByStartAndEnd(content,'<','>'),
            'reposts_count':reposts_count,
            'comments_count':comments_count,
            'attitudes_count':attitudes_count,
            'comments':list,
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
        s = s.replace(x3,"")
    return s



if __name__ == '__main__':
    list=['2019-12-9','2019-12-11','2019-12-13','2019-12-15','2019-12-17','2019-12-19','2019-12-21','2019-12-23','2019-12-25','2019-12-27','2019-12-29']
    list1=[]
    for i in range(1,7):
        for k in range(1,31,2):
            list1.append('2020-'+str(i)+'-'+str(k))
    for item in list1:
        for j in range(1,9):
            get_data_from(start_url+item+':'+item+'&Refer=g&page=',j,item)
#get_data_from('https://s.weibo.com/weibo?q=%E7%96%AB%E6%83%85&typeall=1&suball=1&timescope=custom:2019-12-17:2019-12-17&Refer=g&page=',1,'2019-12-17')