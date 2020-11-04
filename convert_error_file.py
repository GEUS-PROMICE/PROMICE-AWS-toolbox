# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %(username)s

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import Counter
import math
import pytz
import os

#%% Pressure transducer error data
pres_trans_err = pd.read_csv('metadata/pres_trans_err.csv',sep='\s*,\s*',engine='python')
pres_trans_err.set_index(['site', 'year'],inplace=True,drop=False)
pres_trans_err.sort_index(inplace=True)

pres_trans_err['t0'] = [pd.to_datetime(str(t)).tz_localize('UTC').isoformat() for t in ((np.asarray(pres_trans_err['year'], dtype='datetime64[Y]')-1970)+(np.asarray(pres_trans_err['err_start'], dtype='timedelta64[D]')-1))]

pres_trans_err['t1'] = [pd.to_datetime(str(t)).tz_localize('UTC').isoformat() for t in ((np.asarray(pres_trans_err['year'], dtype='datetime64[Y]')-1970)+(np.asarray(pres_trans_err['err_end'], dtype='timedelta64[D]')-1))]

pres_trans_err['variable'] = "DepthPressureTransducer_Cor(m)"
pres_trans_err['flag'] = "CHECKME"
pres_trans_err['comment'] = "manually flagged by bav"
pres_trans_err['URL_graphic'] = "https://github.com/GEUS-PROMICE/AWS-data/blob/main/flags/graphics/" + pres_trans_err.site.values +"_dpt_1.png"

err_file = pres_trans_err.drop(['site', 'year','err_start','err_end'], axis=1)

for site in np.unique(pres_trans_err.site):
    err_file.loc[site].to_csv('metadata/'+site+'.csv',index=False)

#%% Pressure transducer adjust data

pres_trans_adj = pd.read_csv('metadata/pres_trans_adj.csv',sep='\s*,\s*',engine='python')
pres_trans_adj.set_index(['site', 'year'],inplace=True,drop=False)
pres_trans_adj.sort_index(inplace=True)

pres_trans_adj['t0'] = [pd.to_datetime(str(t)).tz_localize('UTC').isoformat() for t in ((np.asarray(pres_trans_adj['year'], dtype='datetime64[Y]')-1970)+(np.asarray(pres_trans_adj['adjust_start'], dtype='timedelta64[D]')-1))]

pres_trans_adj['t1'] = np.NaN

pres_trans_adj['variable'] = "DepthPressureTransducer_Cor(m)"
pres_trans_adj['adjust_function'] = "add"
pres_trans_adj['adjust_value'] = pres_trans_adj['adjust_val']
pres_trans_adj['comment'] = "manually adjusted by bav"
pres_trans_adj['URL_graphic'] = "https://github.com/GEUS-PROMICE/AWS-data/blob/main/flags/graphics/" + pres_trans_adj.site.values +"_dpt_1.png"

err_file = pres_trans_adj.drop(['site', 'year','adjust_start','adjust_val'], axis=1)

for site in np.unique(pres_trans_adj.site):
    err_file.loc[site].to_csv('metadata/flag-fix/'+site+'.csv',index=False)
    
#%% Surface height adjust data

hs_adj = pd.read_csv('metadata/hs_adj.csv',sep='\s*,\s*',engine='python')
hs_adj.set_index(['site', 'year'],inplace=True,drop=False)
hs_adj.sort_index(inplace=True)

hs_adj['t0'] = [pd.to_datetime(str(t)).tz_localize('UTC').isoformat() for t in ((np.asarray(hs_adj['year'], dtype='datetime64[Y]')-1970)+(np.asarray(hs_adj['adjust_start'], dtype='timedelta64[D]')-1))]

hs_adj['t1'] = np.NaN

tmp = ['Snow', 'Surface']
hs_adj['variable'] = [tmp[i-1]+"Height(m)" for i in hs_adj['instr'].values]
hs_adj['adjust_function'] = "add"
hs_adj['adjust_value'] = hs_adj['adjust_val']
hs_adj['comment'] = "manually adjusted by bav"
hs_adj['URL_graphic'] = ["https://github.com/GEUS-PROMICE/AWS-data/blob/main/flag-fix/graphics/" + site +"_hs_"+ str(i) + ".png" 
                         for site, i in zip( hs_adj.site.values,
                                            hs_adj['instr'].values)]

err_file = hs_adj.drop(['site', 'year','adjust_start','adjust_val','instr'], axis=1)

for site in np.unique(hs_adj.site):
    if not os.path.isfile('metadata/flag-fix/'+site+'.csv'):
       err_file.loc[site].to_csv('metadata/flag-fix/'+site+'.csv',index=False)
    else: # else it exists so append without writing the header
       err_file.loc[site].to_csv('metadata/flag-fix/'+site+'.csv',index=False, mode='a', header=False)
    