#!/bin/python
# -*- coding: utf-8 -*-

"""
Zimmer finden - WOHN

This program is intended to be the back-end of a platform aimed at helping students find a place to live in Münster.

Huriel Reichel - huriel.reichel@protonmail.com

First Experiment with WG-Gesucht website

Missing : other related websites

"""

# import required libraries
import requests
import argparse
import datetime
import folium
import pyproj
import pandas as pd
import time as tp
from bs4 import BeautifulSoup
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from scipy.spatial.distance import cdist

# argument parser
pm_argparse = argparse.ArgumentParser()

# argument and parameter directive #
pm_argparse.add_argument( '--date' ,  type=str  , help = 'date of desired move in DD.MM.YEAR format' )
pm_argparse.add_argument( '--price',  type=int ,  help = 'maximum price')
pm_argparse.add_argument( '--output', type=str,   help = 'path to output html directory')
pm_argparse.add_argument( '--poi',    type=str,   help = 'Address of Point of Interest in the format : Street, number. Use brackets! ')

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


# end of function


df_p1 = wggesucht(url1)
df_p2 = wggesucht(url2)
df_p12 = pd.concat([df_p1, df_p2])

# moving date option
if pm_args.date is not None:

    given_time = pm_args.date.replace('.','')

    given_time = datetime.datetime(int(given_time[4:]), int(given_time[2:4]), int(given_time[0:2]), 12, 00)

    given_time = tp.mktime(given_time.timetuple())
  
    df_p12 = df_p12[df_p12['time'] >= given_time]

# price option
if pm_args.price is not None:

    given_price = pm_args.price

    df_p12['price'] = df_p12['price'].astype(int)

    df_p12 = df_p12[df_p12['price'] <= given_price]

# geocoding

print(" \n geocoding... \n ")
locator = Nominatim(user_agent="myGeocoder")
geocode = RateLimiter(locator.geocode, min_delay_seconds=1)

split = df_p12["info"].str.split(",", expand = True)
host = list(split[0])
type = list(split[1])
city = list(split[2])
neigh = list(split[3])
street = list(split[4])
number = list(split[5])
country = ['Germany'] * len(city)

for i in range(len(city)):

    if type[i] == 'Münster':

        street[i] = neigh[i]
        neigh[i] = ''
        
    if city[i] != 'Münster':

        number[i] = street[i]
        street[i] = neigh[i]
        neigh[i] = city[i]
        city[i] = type[i]

    if street[i] == '' and number[i] is not None:

        street[i] = number[i]
        number[i] = ''

    if number[i] is None or number[i] == '':

        number[i] = '00'

    if neigh[i] == '':

        neigh[i] = '00'

df_p12['street'] = street
df_p12['number'] = number

address  = list(map(','.join, zip(street, number, neigh, city, country)))
df_p12['address'] = address
df_p12['location'] = df_p12['address'].apply(geocode)
df_p12['point'] = df_p12['location'].apply(lambda loc: tuple(loc.point) if loc else None)
df_p12 = df_p12.dropna(subset = ['point'])
df_p12[['latitude', 'longitude', 'altitude']] = pd.DataFrame(df_p12['point'].tolist(), index=df_p12.index)

# folium interactive map
locations = df_p12[['latitude', 'longitude']]
locationlist = locations.values.tolist()
links = list(df_p12['link'])
prices = list(df_p12['price'])

# distance to point option
if pm_args.poi is not None:

    print('\n modelling surface of optimal location ... \n ')

    address = pm_args.poi + ', Münster, ' + 'Germany'
    df_poi = pd.DataFrame({'address' : [address]})
    df_poi['location'] = df_poi['address'].apply(geocode)
    df_poi['point'] = df_poi['location'].apply(lambda loc: tuple(loc.point) if loc else None)

    if df_poi['point'] is None:

        print('Address invalid or not found')

    df_poi[['latitude', 'longitude', 'altitude']] = pd.DataFrame(df_poi['point'].tolist(), index=df_poi.index)
    latlong = [df_poi.latitude, df_poi.longitude]

    wgs84 = pyproj.Proj(projparams = 'epsg:4326')
    utm = pyproj.Proj(projparams = 'epsg:32632')

    lon, lat = pyproj.transform(wgs84, utm, df_p12.latitude, df_p12.longitude)
    lon_poi, lat_poi = pyproj.transform(wgs84, utm, df_poi.latitude, df_poi.longitude)


    df_p12['lon'] = lon
    df_p12['lat'] = lat
    df_poi['lat'] = lat_poi
    df_poi['lon'] = lon_poi

    # calculate distance
    m = cdist(df_p12[['lon', 'lat']], df_poi[['lon', 'lat']], 'euclidean')
    df_p12['dist'] = m

    #interpolate distance

### make this popup look better ###
map = folium.Map(location = [51.95371107628213, 7.628077552663438], zoom_start = 13)
for point in range(0, len(locationlist)):
    folium.Marker(locationlist[point], popup=[links[point],prices[point]]).add_to(map)

out_path = pm_args.output + 'wohn.html'
map.save(out_path)

#interpolates value of distance - distance to public transport
#plot surface (quartile - (very far, far, reasonable, close, very close))
#colours for price
#association with links
