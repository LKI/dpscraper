# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import random

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse  # NOQA

logger = logging.getLogger(__name__)


def re_crawl(func):
    crawled = set()

    def wrapper(spider, response):
        """
        :type spider: DPSpider
        :type response: HtmlResponse
        """
        cookies = get_cookies(response.headers.getlist('Set-Cookie') or [])
        if not response.text and response.url not in crawled:
            logging.warning('empty url: {}'.format(response.url))
            crawled.add(response.url)
            yield response.follow(response.url, spider.parse_shop, dont_filter=True, cookies=cookies)
        else:
            yield from func(spider, response)

    return wrapper


def get_cookies(cookies_data):
    cookies = {}
    for cookie_data in cookies_data:  # type: bytes
        for key, value in (_.split('=', 1) for _ in cookie_data.decode().split('; ')):
            cookies[key] = value
    return cookies


class DPPipeline(object):
    results = []

    def process_item(self, item, _):
        if item:
            self.results.append(dict(item))


class DPSpider(scrapy.Spider):
    name = 'dp'
    start_urls = [
        'http://www.dianping.com/search/category/1/10/r2865g10',
    ]

    def parse(self, response):
        """
        :type response: HtmlResponse
        """
        cookies = get_cookies(response.headers.getlist('Set-Cookie') or [])
        urls = response.xpath(
            '//div[@class="content"]/div/ul/li/div[@class="txt"]/div[@class="tit"]/a[@data-hippo-type="shop"]/@href')
        logger.info(urls.extract())
        # for shop_url in urls:  # type: scrapy.Selector
        #     if 'shop/98376730' in shop_url.extract():  # see http://www.dianping.com/robots.txt
        #         continue
        #     yield response.follow(shop_url, self.parse_shop, cookies=cookies)
        yield response.follow(urls.extract_first(), self.parse_shop, cookies=cookies)

        # next_page = response.xpath('//div[@class="page"]/a[@class="next"]/@href').extract_first()
        # if next_page is not None:
        #     yield response.follow(next_page, self.parse)

    @re_crawl
    def parse_shop(self, response):
        """
        :type response: HtmlResponse
        """
        body = response.xpath('//*[@id="body"]')
        info = body.xpath('//div[@id="basic-info"]')
        addr = info.xpath('div/span[@itemprop="street-address"]')
        breadcrumbs = self.pad(body.xpath('div/div[@class="breadcrumb"]/*/text()').extract())
        data = {
            'shop': self.first(info.xpath('h1[@class="shop-name"]/text()')),
            'phone': self.first(info.xpath('p/span[@itemprop="tel"]/text()')),
            'address': (addr.xpath('text()').extract_first() or addr.xpath('@title').extract_first() or '').strip(),
            'avg': self.first(info.xpath('div[@class="brief-info"]/span[@id="avgPriceTitle"]/text()')),
            'city': breadcrumbs[0],
            'style': breadcrumbs[1],
            'area': breadcrumbs[2],
            'district': breadcrumbs[3],
            'name': breadcrumbs[4],
        }
        yield data

    def parse_index(self, response):
        """ 爬一下主页 刷一下cookie """

    def pad(self, breadcrumbs):
        breadcrumbs = breadcrumbs[:5] + ([''] * (5 - len(breadcrumbs)))
        return [_.strip() for _ in breadcrumbs]

    def first(self, selector):
        return (selector.extract_first() or '').strip()


if __name__ == '__main__':
    user_agents = [
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
        'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
    ]
    user_agent = random.choice(user_agents)
    logger.info(user_agent)
    process = CrawlerProcess({
        'DOWNLOAD_DELAY': 0.5,
        'ITEM_PIPELINES': {'__main__.DPPipeline': 1},
        'USER_AGENT': user_agent,
    })
    process.crawl(DPSpider)
    process.start()
    logger.info(DPPipeline.results)
