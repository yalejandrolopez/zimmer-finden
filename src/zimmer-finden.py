import requests
from bs4 import BeautifulSoup
import argparse
import pandas as pd
import datetime
import time as tp

"""
First Experiment with WG-Gesucht website

Missing : other related websites
"""

pm_argparse = argparse.ArgumentParser()

# argument and parameter directive #
pm_argparse.add_argument( '--date' , type=str  , help='date of desired move in DD.MM.YEAR format' )
pm_argparse.add_argument( '--price',  type=int , help='maximum price')
pm_argparse.add_argument( '--poi', type=int, help='location of point of interest')

# read argument and parameters #
pm_args = pm_argparse.parse_args()

# wg-gesucht websites (WG Query)
url1 = "https://www.wg-gesucht.de/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Munster.91.0+1+2+3.1.0.html?offer_filter=1&city_id=91&noDeact=1&categories%5B%5D=0&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=3&rent_types%5B%5D=2%2C1"

url2 = "https://www.wg-gesucht.de/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Munster.91.0+1+2+3.1.1.html?categories=0%2C1%2C2%2C3&city_id=91&rent_types%5B0%5D=2&rent_types%5B1%5D=1&noDeact=1&img=1"

def wggesucht(url):

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    
    # main cards for iteration
    price_card = soup.find_all('div', class_= 'col-sm-8 card_body')
    span_card = soup.find_all('div', class_= 'col-xs-11')
    name_card = soup.find_all('h3', class_ = 'truncate_title noprint')
    time_card = soup.find_all('div', class_ = 'col-xs-5 text-center')
    
    price = []
    info = []
    name = []
    link = []
    time = []

    #print(name_card)
    for announce in price_card:
        
        announce_price = announce.b.text.replace(' ', '').replace('€', '')

        price.append(announce_price)


    for announce in span_card:

        announce_info = announce.span.text.replace('                        ', '').replace('|', '').replace('\n','').replace('               ', ',').replace('        ', ',').replace(' ', ',').replace(',,,,,,', '')

        info.append(announce_info)


    for announce in name_card:

        announce_name = announce.a.text.replace('\n', "").replace('                            ', '').replace('                        ', '')
        announce_link = list(announce.a.attrs.values())

        name.append(announce_name)
        link.append(announce_link)

    for announce in time_card:

        announce_time = announce.text.replace('\n', '').replace('  ', '').replace('ab', '').replace('.', '')[0:8]

        date_time = datetime.datetime(int(announce_time[4:]), int(announce_time[2:4]), int(announce_time[0:2]), 12, 00)

        time.append(tp.mktime(date_time.timetuple()))
  
    # clear add
    if (len(name) == len(price) == len(info)) == False :

        price = price[1: ]

        print('\n add removed \n')

        #print('\n', name, '\n', price, '\n', info, '\n')

    # compose data frame
    flat_link = [item for sublist in link for item in sublist]
    domain = ['https://www.wg-gesucht.de'] * len(link)

    link = list(map(''.join, zip(domain, flat_link)))
    zipped = list(zip(name, price, info, link, time))
    df = pd.DataFrame(zipped, columns = ['title', 'price', 'info', 'link', 'time'])

    return( df )

df_p1 = wggesucht(url1)
df_p2 = wggesucht(url2)
df_p12 = pd.concat([df_p1, df_p2])

# moving date option
if pm_args.date is not None:

    given_time = pm_args.date.replace('.','')

    given_time = datetime.datetime(int(given_time[4:]), int(given_time[2:4]), int(given_time[0:2]), 12, 00)

    given_time = tp.mktime(given_time.timetuple())
  
    df_p12 = df_p12[df_p12['time'] >= given_time]

# moving date option
if pm_args.price is not None:

    given_price = pm_args.price

    df_p12['price'] = df_p12['price'].astype(int)

    df_p12 = df_p12[df_p12['price'] <= given_price]

print(df_p12)

    # geocode
    # option : distance to point
    # prelimanry plot before leaflet (or other)
