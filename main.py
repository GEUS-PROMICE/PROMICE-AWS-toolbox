# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 20:00:14 2020

@author: bav
"""
# %matplotlib inline
# %matplotlib qt
import os, sys
import PROMICE_lib as pl
import matplotlib.pyplot as plt

try:
    os.mkdir('figures')
    os.mkdir('out')
except:
    print('figures and output folders already exist')

# sys.stdout = open("Report.md", "w")

path_to_PROMICE = 'C:/Users/bav/OneDrive - Geological survey of Denmark and Greenland/Code/AWS_Processing/Input/PROMICE/'

#load PROMICE dataset for a given station, all available years
PROMICE_stations = [('EGP',(75.6247,-35.9748), 2660),  #OK
                    # ('KAN_B',(67.1252,-50.1832), 350), 
                    # ('KAN_L',(67.0955,-35.9748), 670), #Height sensor boom unusable, Height stake do not capture winter accumulation
                    # ('KAN_M',(67.0670,-48.8355), 1270), # minor adjustment left
                    ('KAN_U',(67.0003,-47.0253), 1840), # OK
                    # ('KPC_L',(79.9108,-24.0828), 370),
                    # ('KPC_U',(79.8347,-25.1662), 870), # pressure transducer not working
                    # ('MIT',(65.6922,-37.8280), 440), # ok minor adjustment left
                    # ('NUK_K',(64.1623,-51.3587), 710), 
                    # ('NUK_L',(64.4822,-49.5358), 530),
                    # ('NUK_U',(64.5108,-49.2692), 1120),
                    # ('QAS_L',(61.0308,-46.8493), 280),
                    # ('QAS_M',(61.0998,-46.8330), 630), 
                    # ('QAS_U',(61.1753,-46.8195), 900), 
                    # ('SCO_L',(72.2230,-26.8182), 460),
                    # ('SCO_U',(72.3933,-27.2333), 970),
                    # ('TAS_A',(65.7790,-38.8995), 890),
                    # ('TAS_L',(65.6402,-38.8987), 250),
                    # ('THU_L',(76.3998,-68.2665), 570),
                    # ('THU_U',(76.4197,-68.1463), 760),
                    # ('UPE_L',(72.8932,-54.2955), 220), 
                    # ('UPE_U',(72.8878,-53.5783), 940)
                   ]

for ws in PROMICE_stations:
    site = ws[0]
    print('# '+site)
    df =pl.load_promice(path_to_PROMICE+site+'_hour_v03.txt')
    
    print('## Removing erroneous data at '+site)
    df_out = pl.remove_flagged_data(df, site, plot=True)
    
    print('## Adjusting data at '+site)
    df_v4 = pl.adjust_data(df_out, site)
               
    # # combining pressure transducer and surface height to reconstruct the surface heigh
    print('## Summarizing surface height at '+site)
    df_v4 = pl.combine_hs_dpt(df_v4, site)
     
    if len(df)>0:
        # saving to file
        df_v4.fillna(-999).to_csv('out/'+site+'_hour_v03_L3.txt', sep="\t")   

# %run tocgen.py Report.md Report_toc.md

# sys.stdout.close()
