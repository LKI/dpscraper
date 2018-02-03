# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import scrapy
from scrapy.http import HtmlResponse  # NOQA


class DistrictSpider(scrapy.Spider):
    name = 'district'
    start_urls = [
        'http://www.dianping.com/search/category/1/10/r2865g10',
    ]
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
    }

    def parse(self, response):
        """
        :type response: HtmlResponse
        """
        urls = response.xpath('//div[@class="content"]/div/ul/li/div[@class="txt"]/div[@class="tit"]/a/@href')
        for shop_url in urls:  # type: scrapy.Selector
            yield response.follow(shop_url, self.parse_shop)

        next_page = response.xpath('//div[@class="page"]/a[@class="next"]/@href').extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    def pad(self, breadcrumbs):
        breadcrumbs = breadcrumbs[:5] + ([''] * (5 - len(breadcrumbs)))
        return [_.strip() for _ in breadcrumbs]

    def parse_shop(self, response):
        """
        :type response: HtmlResponse
        """
        body = response.xpath('//*[@id="body"]')
        info = body.xpath('//div[@id="basic-info"]')
        addr = info.xpath('div/span[@itemprop="street-address"]')
        breadcrumbs = self.pad(body.xpath('div/div[@class="breadcrumb"]/*/text()').extract())
        yield {
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

    def first(self, selector):
        return (selector.extract_first() or '').strip()
