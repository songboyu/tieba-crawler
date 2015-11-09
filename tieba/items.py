# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field

class TiebaThreadItem(Item):
    thread_id = Field()
    tieba_id = Field()
    reply_num = Field()
    title = Field()
    abstract = Field()
    url = Field()
    author = Field()
    latest_replyer = Field()
    latest_reply_time = Field()

class TiebaPostItem(Item):
    post_id = Field()
    is_anonym = Field()
    thread_id = Field()
    floor = Field()
    content = Field()
    comment_num = Field()
    client = Field()
    reply_time = Field()
    user_id = Field()
    user_name = Field()

class TiebaCommentItem(Item):
    comment_id = Field()
    thread_id = Field()
    post_id = Field()
    user_id = Field()
    user_name = Field()
    content = Field()
    comment_time = Field()