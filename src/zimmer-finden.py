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
import webbrowser
import math
import pandas as pd
import time as tp
import numpy as np
import matplotlib.pyplot as plt #to be removed
from bs4 import BeautifulSoup
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from pyproj import Transformer
from osgeo import gdal
from osgeo import gdal_array
from osgeo import osr
from matplotlib.colors import ListedColormap
from branca.element import Template, MacroElement

# argument parser
pm_argparse = argparse.ArgumentParser()

# argument and parameter directive #
pm_argparse.add_argument( '--date' ,  type=str  , help = 'date of desired move in DD.MM.YEAR format' )
pm_argparse.add_argument( '--price',  type=int ,  help = 'maximum price')
pm_argparse.add_argument( '--output', type=str,   help = 'path to output html directory')
pm_argparse.add_argument( '--poi',    type=str,   help = 'Address of Point of Interest in the format : Street, number. Use quote! ')
pm_argparse.add_argument( '--write',  type=int,   default = 1, help = 'Write or not csv. 0 to false and 1 to true (default)')

# read argument and parameters #
pm_args = pm_argparse.parse_args()

# wg-gesucht websites (WG Query)
url1 = "https://www.wg-gesucht.de/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Munster.91.0+1+2+3.1.0.html?offer_filter=1&city_id=91&noDeact=1&categories%5B%5D=0&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=3&rent_types%5B%5D=2%2C1"

url2 = "https://www.wg-gesucht.de/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Munster.91.0+1+2+3.1.1.html?categories=0%2C1%2C2%2C3&city_id=91&rent_types%5B0%5D=2&rent_types%5B1%5D=1&noDeact=1&img=1"

def dist(x, y, x0, y0) :

    d = math.sqrt( (x - x0) ** 2 + (y - y0) ** 2)

    return (d)

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

def distance_matrix(x0, y0, x1, y1):
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T

    d0 = np.subtract.outer(obs[:,0], interp[:,0])
    d1 = np.subtract.outer(obs[:,1], interp[:,1])

    return np.hypot(d0, d1)

def idw(x, y, z, xi, yi):
    dist = distance_matrix(x,y, xi,yi)

    weights = dist ** -4
    weights /= weights.sum(axis=0)

    zi = np.dot(weights.T, z)

    return zi

# end of functions

# web scrapping
df_p1 = wggesucht(url1)
df_p2 = wggesucht(url2)
df_p12 = pd.concat([df_p1, df_p2])

# moving date option
if pm_args.date is not None:

    given_time = pm_args.date.replace('.','')

    given_time = datetime.datetime(int(given_time[4:]), int(given_time[2:4]), int(given_time[0:2]), 12, 00)

    given_time = tp.mktime(given_time.timetuple())
  
    #df_p12 = df_p12[df_p12['time'] >= given_time] #if you want to exclude points with later moving dates

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

# Optimal location
locations = df_p12[['latitude', 'longitude']]
locationlist = locations.values.tolist()
links = list(df_p12['link'])
prices = list(df_p12['price'])

transformer = Transformer.from_crs("epsg:4326", "epsg:32632")
lon, lat = transformer.transform(df_p12.latitude, df_p12.longitude)
    
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

    lon_poi, lat_poi = transformer.transform(df_poi.latitude, df_poi.longitude)

    # calculate distance
    d = []

    for i in range(len(lon)):

        d.append(dist(lon[i], lat[i], lat_poi, lon_poi))

    df_p12['dist'] = d

# calculate optimal place index
if pm_args.date is not None and pm_args.poi is not None:

    df_p12['time_w'] = df_p12['time'].astype(float) - given_time
    df_p12['index'] = df_p12['price'].astype(float) + df_p12['dist'].astype(float) + df_p12['time_w'].astype(float)

elif pm_args.date is not None and pm_args.poi is None:

    df_p12['time_w'] = df_p12['time'].astype(float) - given_time
    df_p12['index'] = df_p12['price'].astype(int) + df_p12['time_w'].astype(float)

elif pm_args.date is None and pm_args.poi is not None:

    df_p12['index'] = df_p12['price'].astype(int) + df_p12['dist'].astype(float)

else:

    df_p12['index'] = df_p12['price'].astype(int)

df_p12['index'] =  (( df_p12['index'] - df_p12['index'].min() ) / ( df_p12['index'].max() - df_p12['index'].min() ))

#write csv with locations and data
if pm_args.write != 0:

    filename = pm_args.output + str(int(tp.time())) + '-wohn.csv'
    df_p12.to_csv(filename)

#interpolate index for best place

# sampling grid
xmin = int(394000) 
width = int(30000)
xmax = int(xmin + width)
ymin = int(5737000) 
height = int(32000) 
ymax = int(ymin + height)

x = lon
y = lat
z = list(df_p12['index'])

# grid resolution
nx = int(width/200)
ny = int(height/200)

xi = np.linspace(xmin, xmax, nx)
yi = np.linspace(ymin, ymax, ny)
xi, yi = np.meshgrid(xi, yi)
xi, yi = xi.flatten(), yi.flatten()

# Compute Inverse Distance Weighting
grid1 = idw(x,y,z,xi,yi)
grid1 = grid1.reshape((ny, nx))

# define and export raster - should be optional

nrows,ncols = np.shape(grid1)
geotransform=(xmin,nx,0,ymax,0,-ny)
filename = pm_args.output + str(int(tp.time())) + '-wohn.tif'
output_raster = gdal.GetDriverByName('GTiff').Create(filename, ncols, nrows, 1, gdal.GDT_Float32)
output_raster.SetGeoTransform(geotransform)  
srs = osr.SpatialReference()                 
srs.ImportFromEPSG(32632)
output_raster.SetProjection( srs.ExportToWkt() )    
output_raster.GetRasterBand(1).WriteArray(grid1)  
output_raster.FlushCache()

rst = gdal.Warp('', output_raster, dstSRS='EPSG:4326', format='VRT',
               outputType=gdal.GDT_Float32)
geotransform = rst.GetGeoTransform()
cols = rst.RasterXSize 
rows = rst.RasterYSize 
xmin=geotransform[0]
ymax=geotransform[3]
xmax=xmin+cols*geotransform[1]
ymin=ymax+rows*geotransform[5]

# folium interactive map
### make this popup look better ###
map = folium.Map(location = [51.95371107628213, 7.628077552663438], zoom_start = 13)

for point in range(0, len(locationlist)):

    folium.Marker(locationlist[point],
                  popup=folium.Popup(links[point] + '<br>' + 'Price : €' + prices[point], max_width = 3000),
                  icon=folium.Icon(color="blue",icon="home", prefix='fa')).add_to(map)

pal = ListedColormap(["darkred", "red", "seashell", "lightgreen", "forestgreen"])

folium.raster_layers.ImageOverlay(
    image=grid1,
    opacity = 0.5,
    bounds =[[ymin, xmin], [ymax, xmax]],
    colormap=pal).add_to(map)

# legend
template = """
{% macro html(this, kwargs) %}

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WOHN - Find your home in Münster</title>
  <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

  <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
  <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
  
  <script>
  $( function() {
    $( "#maplegend" ).draggable({
                    start: function (event, ui) {
                        $(this).css({
                            right: "auto",
                            top: "auto",
                            bottom: "auto"
                        });
                    }
                });
});

  </script>
</head>
<body>

 
<div id='maplegend' class='maplegend' 
    style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
     border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
     
<div class='legend-title'>Index of Suitability</div>
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li><span style='background:darkred;opacity:0.7;'></span>Very Bad</li>
    <li><span style='background:red;opacity:0.7;'></span>Bad</li>
    <li><span style='background:seashell;opacity:0.7;'></span>Medium</li>
    <li><span style='background:lightgreen;opacity:0.7;'></span>Good</li>
    <li><span style='background:forestgreen;opacity:0.7;'></span>Very Good</li>
  </ul>
</div>
</div>
 
</body>
</html>

<style type='text/css'>
  .maplegend .legend-title {
    text-align: left;
    margin-bottom: 5px;
    font-weight: bold;
    font-size: 90%;
    }
  .maplegend .legend-scale ul {
    margin: 0;
    margin-bottom: 5px;
    padding: 0;
    float: left;
    list-style: none;
    }
  .maplegend .legend-scale ul li {
    font-size: 80%;
    list-style: none;
    margin-left: 0;
    line-height: 18px;
    margin-bottom: 2px;
    }
  .maplegend ul.legend-labels li span {
    display: block;
    float: left;
    height: 16px;
    width: 30px;
    margin-right: 5px;
    margin-left: 0;
    border: 1px solid #999;
    }
  .maplegend .legend-source {
    font-size: 80%;
    color: #777;
    clear: both;
    }
  .maplegend a {
    color: #777;
    }
</style>
{% endmacro %}"""

macro = MacroElement()
macro._template = Template(template)

map.get_root().add_child(macro)

out_path = pm_args.output + 'wohn.html'
map.save(out_path)
webbrowser.open(out_path)

#association with links
#men or woman desired for room
