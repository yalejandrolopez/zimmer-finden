#!/bin/python
# -*- coding: utf-8 -*-

"""
Zimmer finden - WOHN

This program is intended to be the back-end of a platform aimed at helping students find a place to live in Münster.

This specific code aims at creating a time-series of room and flat prices in Münster

Huriel Reichel - huriel.reichel@protonmail.com

"""
# import required libraries
import argparse
import glob
import pandas as pd
# argument parser
pm_argparse = argparse.ArgumentParser()

# argument and parameter directive #
pm_argparse.add_argument( '--dir' ,  type=str  , help = 'input directory path' )

# read argument and parameters #
pm_args = pm_argparse.parse_args()

# bash read csvs
dt = pd.DataFrame()
for file_name in glob.glob(pm_args.dir+'*.csv'):
    x = pd.read_csv(file_name, low_memory=False)
    dt = pd.concat([dt,x],axis=0)

print(dt)

# get prices

# plot and save plot
