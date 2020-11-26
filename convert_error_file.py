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
   
#%% Maintenance file
site
xl = pd.ExcelFile('metadata/maintenance.xlsx')
xl.sheet_names  # see all sheet names
for sheet_name in xl.sheet_names[0:-1]:
    print(sheet_name)
    site = sheet_name
    if site == 'SouthDome':
        site = 'South Dome'
    if site == 'SwissCamp':
        site = 'Swiss Camp'
        
    maintenance = xl.parse(sheet_name)
    maintenance.drop(['T1 before (cm)',
           'T1 after (cm)', 'T2 before (cm)', 'T2 after (cm)', 'W1 before (cm)',
           'W1 after (cm)', 'W2 before (cm)', 'W2 after (cm)', 'NewDepth1 (m)',
           'NewDepth2 (m)', 'NewDepth3 (m)', 'NewDepth4 (m)', 'NewDepth5 (m)',
           'NewDepth6 (m)', 'NewDepth7 (m)', 'NewDepth8 (m)', 'NewDepth9 (m)',
           'NewDepth10 (m)'],axis = 1, inplace = True)
    
    try: 
        maintenance['t0'] = pd.to_datetime(maintenance['Date (dd-mm-yyyy HH:MM)'],
                                           format= '%Y-%m-%d %H:%M:%S')
    except:
        maintenance['t0'] = pd.to_datetime(maintenance['Date (dd-mm-yyyy HH:MM)'],
                                           format= '%d-%b-%Y %H:%M:%S')
    maintenance.set_index('t0',inplace=True,drop=False)
    maintenance['t1'] = ''
    
    tmp1= maintenance[['Date (dd-mm-yyyy HH:MM)', 'reported', 'SR1 before (cm)',
                       'SR1 after (cm)', 't0', 't1']].copy()
    tmp1['variable']= 'SnowHeight(m)'
    tmp2= maintenance[['Date (dd-mm-yyyy HH:MM)', 'reported', 
                       'SR2 before (cm)', 'SR2 after (cm)', 't0', 't1']].copy()
    tmp2['variable']= 'SurfaceHeight(m)'
    tmp2=tmp2.rename(columns={'SR2 before (cm)': 'SR1 before (cm)'})
    tmp2=tmp2.rename(columns={'SR2 after (cm)': 'SR1 after (cm)'})
    maintenance = tmp1.append(tmp2)
    
    maintenance['adjustement_function'] = 'add'
    maintenance['adjustement_value'] = (maintenance['SR1 after (cm)']-maintenance['SR1 before (cm)'])/100
    
    maintenance['comment'] = ''
    for i in range(maintenance.shape[0]):
        if maintenance['reported'][i]=='y':
            maintenance.iloc[i, maintenance.columns.get_loc("comment")] = 'Reported visit. SR1 height before/after (m): '+ \
            str(maintenance['SR1 before (cm)'][i]/100)+'/'+str(maintenance['SR1 after (cm)'][i]/100)
        else:
            maintenance.iloc[i, maintenance.columns.get_loc("comment")] = 'Not reported. Manual shift suggested by bav.'
            
    maintenance.drop(['Date (dd-mm-yyyy HH:MM)', 'reported', 'SR1 before (cm)',
           'SR1 after (cm)'],axis = 1,inplace=True)
    
    maintenance=maintenance.loc[~np.isnan(maintenance['adjustement_value']).values,:]
    maintenance=maintenance.loc[~(maintenance['adjustement_value'].values==0),:]
    maintenance['t0'] = [t.tz_localize('UTC').isoformat() for t in maintenance['t0']]
                       
    if not os.path.isfile('metadata/flag-fix/'+site+'.csv'):
       maintenance.to_csv('metadata/flag-fix/'+site+'.csv',index=False)
    else: # else it exists so append without writing the header
       maintenance.to_csv('metadata/flag-fix/'+site+'.csv',index=False, mode='a', header=False)
        