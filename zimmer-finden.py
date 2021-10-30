import requests
from bs4 import BeautifulSoup

url = "https://www.wg-gesucht.de/wg-zimmer-in-Munster.91.0.1.0.html"
#url = "https://www.wg-gesucht.de/wg-zimmer-in-Munster-Mauritz.9003582.html"

response = requests.get(url)
soup = BeautifulSoup(response.content, "lxml")
tags = soup.find_all('h3') 

ls = []

for announce in tags:

    for i in range(len(announce)):

        ls.append(announce.text)


announce_card = soup.find_all('div', class_= 'col-sm-8 card_body')

span_card = soup.find_all('div', class_= 'col-xs-11')

#print(span_card)

link = []
price = []

for announce in announce_card:

    announce_link = announce.a.text.replace(' ', '').replace('\n', '')

    announce_price = announce.b.text.replace(' ', '')

    link.append(announce_link)

    price.append(announce_price)

info = []

for subannounce in span_card:

    #print(subannounce)

    announce_info = subannounce.span.text.replace('                        ', '').replace('|', '').replace('\n','').replace('               ', ',').replace('        ', ',').replace(' ', ',').replace(',,,,,,', '')

    info.append(announce_info)

print(len(link) == len(price) ==len(info))



