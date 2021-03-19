import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import AirbankItem
from itemloaders.processors import TakeFirst
import json
import requests
from w3lib.html import remove_tags
pattern = r'(\xa0)?'

url = "https://www.airbank.cz/graphql"

payload = "[{{\"operationName\": \"Articles\",\"variables\": {{\"offset\": {},\"categoryAplCode\": \"\"}},\"query\": \"query Articles($limit: Int = 8, $offset: Int = 0, $categoryAplCode: String = \\\"\\\") {{\\n  articles(limit: $limit, offset: $offset, categoryAplCode: $categoryAplCode) {{\\n    aplCode\\n    name\\n    url\\n    publishDate\\n    perex\\n    isTop\\n    isBig\\n    categories {{\\n      aplCode\\n      name\\n      __typename\\n    }}\\n    images {{\\n      isMain\\n      image\\n      description\\n      __typename\\n    }}\\n    __typename\\n  }}\\n}}\\n\"\r\n    }}\r\n]"
headers = {
    'authority': 'www.airbank.cz',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': '*/*',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'content-type': 'application/json',
    'origin': 'https://www.airbank.cz',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.airbank.cz/pro-novinare/',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': 'mid=54184023884276412562562707755250259263; device_view=not_mobile; _fbp=fb.1.1614931950630.342873960; accepted-cookies=604b0b604a21f0e7ae70787ad4a4b7c914941ea9; AMCVS_2CB527E253DF73D80A490D4E%40AdobeOrg=1; AMCV_2CB527E253DF73D80A490D4E%40AdobeOrg=-1124106680%7CMCIDTS%7C18706%7CMCMID%7C54184023884276412562562707755250259263%7CMCAAMLH-1616763004%7C6%7CMCAAMB-1616763004%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1616165404s%7CNONE%7CvVersion%7C5.2.0; s_firstPage=visited; s_cc=true; s_prop14=web%3Apro-novinare; s_sq=brussweb%3D%2526c.%2526a.%2526activitymap.%2526page%253Dweb%25253Apro-novinare%2526link%253DNA%2525C4%25258C%2525C3%25258DST%252520DAL%2525C5%2525A0%2525C3%25258D%2526region%253Dapp%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c%2526pid%253Dweb%25253Apro-novinare%2526pidt%253D1%2526oid%253DfunctionTr%252528%252529%25257B%25257D%2526oidt%253D2%2526ot%253DSUBMIT'
}


class AirbankSpider(scrapy.Spider):
    name = 'airbank'
    start_urls = ['https://www.airbank.cz/pro-novinare/']
    offset = 0

    def parse(self, response):
        data = requests.request("POST", url, headers=headers, data=payload.format(self.offset))
        data = json.loads(data.text)
        for index in range(len(data['data']['articles'])):
            link = data['data']['articles'][index]['url']
            yield response.follow(link, self.parse_post)

        if not len(data['data']['articles']) == 0:
            self.offset += 8
            yield response.follow(response.url, self.parse, dont_filter=True)

    def parse_post(self, response):
        date = ''.join(response.xpath('//p[@class="css-1jtcnrz"]/text()').get().split())
        title = response.xpath('//h1/text()').get()
        content = response.xpath('//p[@class="css-1od0us4"]//text()').getall() + response.xpath('//div[@class="css-9e33z6"]//text()').getall()
        if not content:
            content = response.xpath('//p[@class="css-1od0us4"]//text()').getall() + response.xpath('//div[@class="css-9e33z6"]//text()').getall()

        content = [p.strip() for p in content if p.strip()]
        content = remove_tags(re.sub(pattern, "",' '.join(content)))

        item = ItemLoader(item=AirbankItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()
