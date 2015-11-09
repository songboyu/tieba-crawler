# -*- coding: utf-8 -*-
import json
import datetime

from scrapy import Spider, Request
from scrapy import log
from tieba.items import TiebaThreadItem
from tieba.items import TiebaPostItem
from tieba.items import TiebaCommentItem

import yaml
import MySQLdb

class TiebaSpider(Spider):
    name = 'tieba'
    allow_domains = ['http://tieba.baidu.com/']
    end_page = 10
    def __init__(self):
        CONFIG = yaml.load(open('config.yaml'))
        self.con = MySQLdb.connect(CONFIG['db']['host'],
                                   CONFIG['db']['user'],
                                   CONFIG['db']['password'],
                                   CONFIG['db']['database'],
                                   charset='utf8')
        self.cur = self.con.cursor()
        self.cur.execute('select * from sites')
        self.tieba = self.cur.fetchall()

        self.cur.close()
        self.con.close()

    def start_requests(self):
        for i in range(len(self.tieba)):
            for pn in range(self.end_page):
                # log.msg(self.tieba[i][2] + '&pn=' +str(pn*50), level=log.INFO)
                yield Request(self.tieba[i][2] + '&pn=' +str(pn*50), 
                    callback=self.parse_thread_item, 
                    meta={'tieba_id': self.tieba[i][0]},
                    priority=10)

    def parse_thread_item(self, response):
        articles = response.css('li.j_thread_list')
        tieba_id = response.meta['tieba_id']
        for article in articles:
            item = TiebaThreadItem()

            item['tieba_id'] = tieba_id

            r = article.css('span.threadlist_rep_num::text').extract()
            if r: item['reply_num'] = r[0]

            r  = article.css('a.j_th_tit::text').extract()
            if r: item['title'] = r[0]

            r  = article.css('div.threadlist_abs_onlyline::text').extract()
            if r: item['abstract'] = r[0].strip()

            r  = article.css('a.j_th_tit::attr(href)').extract()
            if not r: continue

            item['url'] = 'http://tieba.baidu.com'+r[0]
            item['thread_id'] = r[0][3:]

            r = article.css('span.tb_icon_author>a::text').extract()
            if r: item['author'] = r[0]

            r = article.css('span.tb_icon_author_rely>a::text').extract()
            if r: item['latest_replyer'] = r[0]

            r = article.css('span.threadlist_reply_date::text').extract()
            if r: 
                t = r[0].strip()
                if ':' in t:
                    item['latest_reply_time'] = str(datetime.date.today())+' '+t
                elif '-' in t:
                    item['latest_reply_time'] = str(datetime.date.today().year)+'-'+t


            yield item
            yield Request(item['url'], 
                    callback=self.get_posts, 
                    meta={'thread_id': item['thread_id']},
                    priority=20)

    def get_posts(self, response):
        page_count = response.css('span.red::text').extract()[-1]
        self.parse_post_item(response)

        for i in range(2, int(page_count)+1):
            yield Request(response.url+'?pn='+str(i), 
                    callback=self.parse_post_item, 
                    meta={'thread_id': response.meta['thread_id'], 'pn': i},
                    priority=20)


    def parse_post_item(self, response):
        replys = response.css('div#j_p_postlist div.l_post')
        forum_id = response.xpath('//html').re(r'"forum_id":(\d+),')[0]
        thread_id = response.meta['thread_id']
        pn = response.meta['pn']
        for reply in replys:
            data = json.loads(reply.css('::attr(data-field)').extract()[0])
            item = TiebaPostItem()

            item['post_id'] = data['content']['post_id']
            item['is_anonym'] = data['content']['is_anonym']
            item['thread_id'] = thread_id

            item['floor'] = data['content']['post_no']
            item['comment_num'] = data['content']['comment_num']
            if item['is_anonym'] != 1:
                item['user_id'] = data['author']['user_id']
            item['user_name'] = data['author']['user_name']

            r = reply.css('a.p_tail_wap::text').extract()
            if r: item['client'] = r[0].strip()

            try:
                item['content'] = data['content']['content']
            except:
                r = reply.css('div.d_post_content')
                if r: item['content'] = r[0].re(r'>(.*)</div')[0].strip()

            try:
                item['reply_time'] = data['content']['date']
            except:
                r  = reply.css('span.j_reply_data::text').extract()
                if r: item['reply_time'] = r[0].strip()

            yield item
            yield Request('http://tieba.baidu.com/p/totalComment?tid='+str(thread_id)+'&fid='+str(forum_id)+'&pn='+str(pn)+'&see_lz=0', 
                    callback=self.parse_comment_item, 
                    priority=30)

    def parse_comment_item(self, response):
        d = json.loads(response.body)
        a = d['data']['comment_list']
        if isinstance(a,list):  return

        for b in a.values():
            for c in b['comment_info']:
                item = TiebaCommentItem()

                item['comment_id'] = c['comment_id']
                item['thread_id'] = c['thread_id']
                item['post_id'] = c['post_id']
                item['user_id'] = c['user_id']
                item['user_name'] = c['username']
                item['content'] = c['content']
                timeStamp = c['now_time']
                dateArray = datetime.datetime.utcfromtimestamp(timeStamp)
                comment_time = dateArray.strftime("%Y-%m-%d %H:%M:%S")
                item['comment_time'] = comment_time

                yield item