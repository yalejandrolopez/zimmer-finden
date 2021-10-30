import requests
from bs4 import BeautifulSoup
import argparse

"""
First Experiment with WG-Gesucht website

Missing : other related websites
"""
if __name__ == "__main__":

    pm_argparse = argparse.ArgumentParser()

    # argument and parameter directive #
    pm_argparse.add_argument( '--startDate' , type=str  , help='date of desired move in DD.MM.YEAR format' )
    pm_argparse.add_argument( '--price',  type=int , help='maximum price')
    pm_argparse.add_argument( '--poi', type=int, help='location of point of interest')

    # read argument and parameters #
    pm_args = pm_argparse.parse_args()

    # wg-gesucht websites (WG Query)
    url = "https://www.wg-gesucht.de/wg-zimmer-in-Munster.91.0.1.0.html"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")

    # main cards for iteration
    announce_card = soup.find_all('div', class_= 'col-sm-8 card_body')
    span_card = soup.find_all('div', class_= 'col-xs-11')

    link = []
    price = []
    info = []

    for announce in announce_card:
        
        announce_link = announce.a.text.replace(' ', '').replace('\n', '')
        announce_price = announce.b.text.replace(' ', '')

        link.append(announce_link)
        price.append(announce_price)

    for subannounce in span_card:

        announce_info = subannounce.span.text.replace('                        ', '').replace('|', '').replace('\n','').replace('               ', ',').replace('        ', ',').replace(' ', ',').replace(',,,,,,', '')

        info.append(announce_info)

    # clear announcement
    if (len(link) == len(price) == len(info)) == False :

        link = link[1: ]
        info = info[1: ]

        print('\n add removed \n')

    # query for 'ein Zimmer Wohnung' #
    # process more pages  - one page enough ?#
    # remove old posts
    # option : moving day
    # option : price
    # geocode
    # option : distance to point
    # prelimanry plot before leaflet (or other)

