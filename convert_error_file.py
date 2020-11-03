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

#%%
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

#%%

