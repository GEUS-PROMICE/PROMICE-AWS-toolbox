# -*- coding: utf-8 -*-
"""
Created on 27-08-2020

Data treatment function for PROMICE weather station

GEUS (Geological Survey of Denmark and Greenland)

Contributors: Adrien Wehrlé, Jason E. Box, B. Vandecrux

"""
# -*- coding: utf-8 -*-

"""
Main functions:    
    - load_data: Load a PROMICE station dataset including all years or selected one(s).
    - dpt_proc: Processes the pressure transducer data
    - hs_proc: Processes the surface height data
Plot functions:
    - plot_pres_trans_adj
    - plot_hs_adj
Tools:
    - smooth
    - hampel
    - firstNonNan
    
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
import datetime
import pytz
import os
import warnings
import difflib as difflib
warnings.filterwarnings("ignore", category=RuntimeWarning)

#%%      

def load_promice(path_promice):
    '''
    Loading PROMICE data for a given path into a DataFrame.
    + adding time index
    + calculating albedo
    + (optional) calculate RH with regard to water
    
    INTPUTS:
        path_promice: Path to the desired file containing PROMICE data [string]
    
    OUTPUTS:
        df: Dataframe containing PROMICE data for the desired settings [DataFrame]
    '''

    df = pd.read_csv(path_promice,delim_whitespace=True)
    df['time'] = df.Year * np.nan
    
    df['time'] = [datetime.datetime(y,m,d,h).replace(tzinfo=pytz.UTC) for y,m,d,h in zip(df['Year'].values,  df['MonthOfYear'].values, df['DayOfMonth'].values, df['HourOfDay(UTC)'].values)]
    df.set_index('time',inplace=True,drop=False)
        
    #set invalid values (-999) to nan 
    df[df==-999.0]=np.nan
    df['Albedo'] = df['ShortwaveRadiationUp(W/m2)'] / df['ShortwaveRadiationDown(W/m2)']
    df.loc[df['Albedo']>1,'Albedo']=np.nan
    df.loc[df['Albedo']<0,'Albedo']=np.nan

    # df['RelativeHumidity_w'] = RH_ice2water(df['RelativeHumidity(%)'] ,
    #                                                    df['AirTemperature(C)'])

    return df
#%% 
def remove_flagged_data(df, site, var_list = ['all'], plot = True):
    '''
    Replace data within a specified variable, between specified dates by NaN.
    Reads from file "metadata/flags/<site>.csv".
    
    INTPUTS:
        df: PROMICE data with time index
        site: string of PROMICE site
        var_list: list of the variables for which data removal should be 
            conducted (default: all)
        plot: whether data removal should be plotted
    
    OUTPUTS:
        promice_data: Dataframe containing PROMICE data for the desired settings [DataFrame]
    '''    
    df_out = df.copy()
    if not os.path.isfile('metadata/flags/'+site+'.csv'):
        print('No erroneous data listed for '+site)
        return df
    
    flag_data = pd.read_csv('metadata/flags/'+site+'.csv')
    
    if var_list[0]=='all':
        var_list =  np.unique(flag_data.variable)
        
    print('Deleting flagged data:')
    for var in var_list:
        if var not in df_out.columns :
            var_new = difflib.get_close_matches(var, df_out.columns, n=1)
            if not var_new:
                print('Warning: '+var+' in erroneous data file but not in PROMICE dataframe')
                continue
            else:
                print('Warning: interpreting '+var+' as '+var_new[0])
                var = var_new[0]
            
        if plot:
            fig = plt.figure(figsize = (15,10))
            df[var].plot(color = 'red',label='bad data')
            
        for t0, t1 in zip(pd.to_datetime(flag_data.loc[flag_data.variable==var].t0), 
                               pd.to_datetime(flag_data.loc[flag_data.variable==var].t1)):
            print(t0, t1, var)
            df_out.loc[t0:t1, var] = np.NaN
            
        if plot:
            df_out[var].plot(label='good data',color='green' )
            plt.title(site)
            plt.xlabel('Year')
            plt.ylabel(var)
            var_save = var
            for c in ['(', ')', '/']:
                var_save=var_save.replace(c,'')
            var_save=var_save.replace('%','Perc')
                
            fig.savefig('figures/'+site+'_'+var_save+'_data_removed.png',dpi=70)
    return df_out
#%%
def smooth(x,window_len=14,window='hanning'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')

    return y[int(window_len/2-1):-int(window_len/2)]

#%% 

def hampel(vals_orig, k=7*24, t0=3):
    '''
    vals: pandas series of values from which to remove outliers
    k: size of window (including the sample; 7 is equal to 3 on either side of value)
    '''
    #Make copy so original not edited
    vals=vals_orig.copy()    
    #Hampel Filter
    L= 1.4826
    rolling_median=vals.rolling(k).median()
    difference=np.abs(rolling_median-vals)
    median_abs_deviation=difference.rolling(k).median()
    threshold= t0 *L * median_abs_deviation
    outlier_idx=difference>threshold
    outlier_idx[0:round(k/2)]=False
    vals.loc[outlier_idx]=np.nan
    return(vals)
#%%
def firstNonNan(listfloats):
  for item in listfloats:
    if math.isnan(item) == False:
      return item
#%%            
def plot_pres_trans_adj(df, year_list,site, ShowInitial = True,tag='1'):
    fs=13
    mpl.rc('xtick', labelsize=fs); mpl.rc('ytick', labelsize=fs); mpl.rc('lines', markersize=3)
    if round(len(year_list)/2) == len(year_list)/2:
        num_plot=len(year_list)/2
    else:
        num_plot=len(year_list)/2+1
    f1, ax=plt.subplots(max(2,int(num_plot)),2,figsize=(15, 15))
    f1.subplots_adjust(hspace=0.2, wspace=0.17,
                       left = 0.08 , right = 0.95 ,
                       bottom = 0.2 , top = 0.9)
    for k,y in enumerate(year_list):
        z = df.loc[df.Year==y, "DepthPressureTransducer_Cor_adj(m)"]
        z_ini = df.loc[df.Year==y, "DepthPressureTransducer_Cor(m)"]
        doy = df.loc[df.Year==y, "DayOfYear"]+df.loc[df.Year==y, "HourOfDay(UTC)"]/24
        
        try: 
            pres_trans_adj = pd.read_csv('metadata/pres_trans_adj.csv',sep='\s*,\s*',engine='python')
            pres_trans_adj.set_index(['site', 'year'],inplace=True)
            pres_trans_adj.sort_index(inplace=True)
            adj_start = pres_trans_adj.loc[(site,y),'adjust_start'].values
        except:                
            adj_start = [np.nan]
        i,j = np.unravel_index(k, ax.shape)

        if ShowInitial:
            ax[i,j].plot(doy, z_ini -firstNonNan(z_ini) +firstNonNan(z),
                         'ro-',  label='Raw')
        ax[i,j].plot(doy, z,'go-', label='Processed')
        for d in adj_start:
            ind = np.logical_and(doy>d-10,doy<d+10) 
            ax[i,j].scatter(d, z.loc[ind].mean(),200,
                      marker="o",facecolors='none', edgecolors='black',
                      linewidths =3, label='Adjustment')
        ax[i,j].set_xlim((0,365))
        if k == 0:
            ax[i,j].legend(loc='upper right')
        ax[i,j].annotate(str(y),
            xy=(0.05, 0.1), xycoords='axes fraction',size = 15)
    f1.text(0.5, 0.95, site, va='center',  size = 20)
    f1.text(0.5, 0.15, 'Day of year', va='center',  size = 20)
    f1.text(0.04, 0.5, 'Ice ablation (m)', va='center', rotation='vertical', size = 20)
    f1.savefig('figures/'+site+'_dpt_'+tag+'.png',dpi=70, bbox_inches='tight')

#%%                   
def dpt_proc(df, year, site, visualisation=True):
    '''
        Processing of Depth Pressure Sensor (DPT) time series using PROMICE 2019-08-02
        datasets.        
        
        INPUTS:
            promice_data: Dataframe imported using load_data() [DataFrame]
            year: Year of promice_data to process [int, list or 'all']
            
        OUTPUTS:
            DPT_proc: Processed ice ablation time series [pandas.series]
            albedo: Albedo time series associated with ice ablation [pandas.series]
            DPT_flag: Assessement of the ease to determine bare ice appearance
                      from ice ablation (0=no data, 1=, 2=low confidence, 
                      3= high confidence) [int]
            albedo_flag: Determines if an albedo time series will be excluded (0)
                          or not (1) [int]
            BID: Bare Ice Day, day of bare ice appearance based on ice ablation [float]
    '''

    if np.sum(np.isnan(df["DepthPressureTransducer_Cor(m)"])) == df["DepthPressureTransducer_Cor(m)"].shape[0]: 
        print("No pressure transducer at "+site)
        return []
    #search for available years
    if year=='all':
        year=list(Counter(df.Year))
    elif isinstance(year, list):
        year=year
    else:
        year=[year]
    year_list = []
        
    # import pdb; pdb.set_trace()
    if "DepthPressureTransducer_Cor_adj(m)" in df.columns:
        print("Warning: overwritting DepthPressureTransducer_Cor_adj(m)")
        df =df.drop(columns="DepthPressureTransducer_Cor_adj(m)", axis=0)
        if "FlagPressureTransducer" in df.columns:
            df =df.drop(columns="FlagPressureTransducer", axis=0)
        
    df.loc[:,"DepthPressureTransducer_Cor_adj(m)"] = np.nan
    df.loc[:,"FlagPressureTransducer"] = np.nan
    # 0 = original data available
    # 1 = no data available
    # 2 = data available but removed manually
    # 3 = data removed by filter
    # 4 = interpolated
    
    for i,y in enumerate(year):
        # import pdb; pdb.set_trace()
        df_y = df.loc[df.Year==y]
        z=df_y["DepthPressureTransducer_Cor(m)"].copy()
        flag = z*0
        flag[np.isnan(z)]=1
        try:
            doy = df_y.DayOfYear.values + df_y["HourOfDay(UTC)"].values/24
            dt = 1
        except:
            doy = df_y.DayOfYear.values
            dt = 24
            
        # removing data manually
        pres_trans_err = pd.read_csv('metadata/pres_trans_err.csv',sep='\s*,\s*',engine='python')
        pres_trans_err.set_index(['site', 'year'],inplace=True)
        pres_trans_err.sort_index(inplace=True)
        if pres_trans_err.index.isin([(site,y)]).any():
            err_start = pres_trans_err.loc[(site,y),'err_start'].values
            err_end = pres_trans_err.loc[(site,y),'err_end'].values
            for k, d in enumerate(err_start):
                z[np.logical_and(doy>=d,doy<=err_end[k])] = np.nan
                flag[np.logical_and(doy>=d,doy<=err_end[k])] = 2
        else:
            print("No erroneous period for "+site+" in "+str(y))
            
        # adjusting pressure transducer depth

        pres_trans_adj = pd.read_csv('metadata/pres_trans_adj.csv',sep='\s*,\s*',engine='python')
        pres_trans_adj.set_index(['site', 'year'],inplace=True)
        pres_trans_adj.sort_index(inplace=True)
        
        if pres_trans_adj.index.isin([(site,y)]).any():
            adj_start = pres_trans_adj.loc[(site,y),'adjust_start'].values
            adj_val = pres_trans_adj.loc[(site,y),'adjust_val'].values
            for k, d in enumerate(adj_start):
                z[doy>=d] = z[doy>=d] + adj_val[k]
        else:
            print("No shift information for "+site+" in "+str(y))
            adj_start = []
            
        # interpolating
        ind1 = np.isnan(z)
        z=z.interpolate(limit=32)
        ind2 = np.isnan(z)
        flag[np.logical_and(ind1,~ind2)] = 4
        
        # filtering
        ind1 = np.isnan(z.values)
        z = hampel(z)    
        z[doy<140] = hampel(z[doy<140] ,k=30*24,t0=1)
        vals = z.values
        vals[np.isnan(vals)]=-9999
        thresh = 10 # m/day
        msk = np.where(np.abs(np.gradient(vals)) >= thresh/24*dt)[0]
        vals[msk] = np.nan
        vals[msk-1] = np.nan
        vals[np.minimum(msk+1,vals.shape[0]-1)] = np.nan
        vals[vals==-9999]=np.nan
        z=pd.Series(vals)
        ind2 = np.isnan(z.values)
        flag[np.logical_and(~ind1,ind2)] = 3
        
        # interpolating
        ind1 = np.isnan(z.values)
        z=z.interpolate(method='linear',limit=32)
        ind2 = np.isnan(z.values)
        flag[np.logical_and(ind1,~ind2)] = 4
        
        z=smooth(z.values)
        if np.sum(~np.isnan(z))>1:
            year_list.append(y)
            z = z - firstNonNan(z)
            
        # updating values in PROMICE table
        df.loc[df.Year==y, "DepthPressureTransducer_Cor_adj(m)"] = z
        df.loc[df.Year==y, "FlagPressureTransducer"] = flag
        
    if visualisation:
        plot_pres_trans_adj(df, year_list,site, ShowInitial = True,tag='1')
        plot_pres_trans_adj(df, year_list,site, ShowInitial = False,tag='2')
    return df

#%%
def plot_hs_adj(df, year_list, site,  
                var1 = "SnowHeight1_adj(m)", var2 = "SnowHeight1(m)",
                tag='1'):
    fs=13
    mpl.rc('xtick', labelsize=fs); mpl.rc('ytick', labelsize=fs); mpl.rc('lines', markersize=3)
    if round(len(year_list)/2) == len(year_list)/2:
        num_plot=len(year_list)/2
    else:
        num_plot=len(year_list)/2+1
    f1, ax=plt.subplots(max(2,int(num_plot)),2,figsize=(25, 15))
    f1.subplots_adjust(hspace=0.2, wspace=0.17,
                       left = 0.08 , right = 0.95 ,
                       bottom = 0.2 , top = 0.9)
    for k,y in enumerate(year_list):
        z1 = df.loc[df.Year==y, var1]
        z2 = df.loc[df.Year==y, var2]
        doy = df.loc[df.Year==y, "DayOfYear"]+df.loc[df.Year==y, "HourOfDay(UTC)"]/24
        
        hs_adj = pd.read_csv('metadata/hs_adj.csv',sep='\s*,\s*',engine='python')
        hs_adj.set_index(['site','year', 'instr'],inplace=True)
        hs_adj.sort_index(inplace=True)
        
        adj_start_1 = [np.nan]
        adj_start_2 = [np.nan]
        if np.any(hs_adj.index.isin([(site,y,1)])):
            adj_start_1 = hs_adj.loc[(site,y,1),'adjust_start'].values
        if np.any(hs_adj.index.isin([(site,y,2)])):
            adj_start_2 = hs_adj.loc[(site,y,2),'adjust_start'].values

        i,j = np.unravel_index(k, ax.shape)
        ax[i,j].plot(doy, z1-firstNonNan(z1),'ro-', label=var1)
        if var2 in df.columns:
            ax[i,j].plot(doy, z2-firstNonNan(z2),  'go-',  label=var2)
        for var in [var1, var2]:
            if var=="SnowHeight1_adj(m)":
                adj_start = adj_start_1
            elif var == "SnowHeight2_adj(m)":
                adj_start = adj_start_2
            else:
                adj_start = [np.nan]
            
            for d in adj_start:
                ind = np.logical_and(doy>d-10,doy<d+10) 
                ax[i,j].scatter(d, df.loc[df.Year==y, var].loc[ind].mean(),200,
                          marker="o",facecolors='none', edgecolors='black',
                          linewidths =3, label='Adjustment')
        ax[i,j].set_xlim((0,365))
        if k == 0:
            ax[i,j].legend(loc='upper right')
        ax[i,j].annotate(str(y),
            xy=(0.05, 0.1), xycoords='axes fraction',size = 15)
    f1.text(0.5, 0.95, site, va='center',  size = 20)
    f1.text(0.5, 0.15, 'Day of year', va='center',  size = 20)
    f1.text(0.04, 0.5, 'Snow height (m)', va='center', rotation='vertical', size = 20)

    f1.savefig('figures/'+site+'_hs_'+tag+'.png',dpi=90, bbox_inches='tight')
    
#%%

def hs_proc(df, site, visualisation=True):
    year_list = np.unique(df.Year)

    df["SnowHeight1(m)"] = 2.6 - df["HeightSensorBoom(m)"] 
    df["SnowHeight2(m)"] = 1 - df["HeightStakes(m)"] 

    z1 = df["SnowHeight1(m)"].copy()
    z2 = df["SnowHeight2(m)"].copy()
    # adjusting pressure transducer depth
    df2 = pd.DataFrame({'year':df.Year, 'month':df.MonthOfYear, 
                         'day':df.DayOfMonth, 'hour':df["HourOfDay(UTC)"]})
    df["time"] = pd.to_datetime(df2)

    # try: 
    hs_adj = pd.read_csv('metadata/hs_adj.csv',sep='\s*,\s*',engine='python')
    hs_adj["time"] = (np.asarray(hs_adj['year'], dtype='datetime64[Y]')-1970)+(np.asarray(hs_adj['adjust_start'], dtype='timedelta64[D]')-1)
    hs_adj.set_index(['site', 'instr'],inplace=True)
    hs_adj.sort_index(inplace=True)
    
    if ~np.isin(site, hs_adj.index.get_level_values('site')):
        print('No adjustment for '+site)
        df["SnowHeight1_adj(m)"] = df["SnowHeight1(m)"]
        df["SnowHeight2_adj(m)"] = df["SnowHeight2(m)"]
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SnowHeight1_adj(m)", var2 = "SnowHeight2_adj(m)",
                    tag='1')
        return df
    
    # first instrument
    if np.isin(1, hs_adj.loc[site].index.get_level_values('instr')):
        adj_start = hs_adj.loc[(site,1),'time'].values
        adj_val = hs_adj.loc[(site,1),'adjust_val'].values
        for k, d in enumerate(adj_start):
            z1.loc[df.time>=d] = z1.loc[df.time>=d] + adj_val[k]
        
    # second instrument
    if np.isin(2, hs_adj.loc[site].index.get_level_values('instr')):
        adj_start = hs_adj.loc[(site,2), 'time'].values
        adj_val = hs_adj.loc[(site,2),'adjust_val'].values
        for k, d in enumerate(adj_start):
            z2.loc[df.time>=d] = z2.loc[df.time>=d] + adj_val[k]
            
    
    if ~np.any(~np.isnan(df["HeightSensorBoom(m)"] )):
        print("No HeightSensorBoom at "+site)
        return

    # interpolating
    z1=z1.interpolate(limit=32)
    z1 = hampel(z1, k = 7*6)    
    vals = z1.values
    vals[np.isnan(vals)]=-9999
    msk = np.where(np.abs(np.gradient(vals)) >= 0.1)[0]
    vals[msk] = np.nan
    vals[np.maximum(msk-1,0)] = np.nan
    vals[np.minimum(msk+1,vals.shape[0]-1)] = np.nan
    vals[vals==-9999]=np.nan
    z1=pd.Series(vals)
    z1 = hampel(z1, k = 7*12,t0=1)    
    df["SnowHeight1_adj(m)"]=z1.values

    # interpolating
    z2=z2.interpolate(limit=32)
    z2 = hampel(z2, k = 7*6)    
    vals = z2.values
    vals[np.isnan(vals)]=-9999
    msk = np.where(np.abs(np.gradient(vals)) >= 0.1)[0]
    vals[msk] = np.nan
    vals[msk-1] = np.nan
    vals[np.minimum(msk+1,vals.shape[0]-1)] = np.nan
    vals[vals==-9999]=np.nan
    z2=pd.Series(vals)
    z2 = hampel(z2, k = 7*12,t0=1)    
    df["SnowHeight2_adj(m)"]=z2.values

    if visualisation:
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SnowHeight1(m)", var2 = "SnowHeight1_adj(m)",
                    tag='1')
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SnowHeight2(m)", var2 = "SnowHeight2_adj(m)",
                    tag='2')
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SnowHeight1_adj(m)", var2 = "SnowHeight2_adj(m)",
                    tag='3')
    return df

#%%
def combine_hs_dpt(df, site):
    # import pdb; pdb.set_trace()

    if "DepthPressureTransducer_Cor_adj(m)" in df.columns:
        z=df["DepthPressureTransducer_Cor_adj(m)"].copy()
        if np.any(~np.isnan(z)):
            doy = df["DayOfYear"]+df["HourOfDay(UTC)"]/24
            ind = np.where(doy == 365)[0]
            for i in ind:
                if np.any(~np.isnan(z[(i+2*24):]))&np.any(~np.isnan(z[:i])):
                    z.iloc[i:] = z.iloc[i:] - firstNonNan(z[(i+2*24):]) + firstNonNan(np.flip(z[:i]))
                    z.iloc[i:(i+2*24)]=np.nan
            vals = z.values
            vals[np.isnan(vals)]=-9999
            msk = np.where(np.abs(np.gradient(vals)) >= 0.1)[0]
            vals[msk] = np.nan
            vals[msk-1] = np.nan
            vals[np.minimum(msk+1,vals.shape[0]-1)] = np.nan
            vals[vals==-9999]=np.nan
            z=pd.Series(vals)
            z.loc[z>0]=np.nan
            z = hampel(z,7*24,1)
            z.interpolate(limit=32,inplace = True)
            df["DepthPressureTransducer_Cor_adj(m)"] = z
        else:
            return df
    else:
        return df
            
    if "SnowHeight1_adj(m)" in df.columns:
        hs1=df["SnowHeight1_adj(m)"].copy()
        if np.any(~np.isnan(hs1)):
            doy = df["DayOfYear"]+df["HourOfDay(UTC)"]/24
            ind = np.where(doy == 260)[0]
            for i in ind:
                # import pdb; pdb.set_trace()
                if np.any(~np.isnan(z.iloc[i:])):
                    hs1.iloc[i:] = hs1.iloc[i:] - firstNonNan(hs1.iloc[i:])  + firstNonNan(z.iloc[i:])
        df["SurfaceHeight1_adj(m)"] = hs1
        
    if "SnowHeight2_adj(m)" in df.columns:
        hs2=df["SnowHeight2_adj(m)"].copy()
        if np.any(~np.isnan(hs1)):
            doy = df["DayOfYear"]+df["HourOfDay(UTC)"]/24
            ind = np.where(doy == 270)[0]
            for i in ind:
                span = 50*24
                hs1_avg = hs1.iloc[i:i+span].mean(skipna=True)
                hs2_avg = hs2.iloc[i:i+span].mean(skipna=True)
                if ~np.isnan(hs2_avg + hs1_avg):     
                    hs2.iloc[i:] = hs2.iloc[i:] - hs2_avg + hs1_avg
            df["SurfaceHeight2_adj(m)"] = hs2

    f1 = plt.figure(figsize=(10, 8))    
    if "DepthPressureTransducer_Cor_adj(m)" in df.columns:
        z=df["DepthPressureTransducer_Cor_adj(m)"].copy()
        if np.any(~np.isnan(z)):
            plt.plot(df["time"], z, label = 'Pressure transducer')
            
    if "SurfaceHeight1_adj(m)" in df.columns:
        if np.any(~np.isnan(df["SurfaceHeight1_adj(m)"])):
            plt.plot(df["time"], df["SurfaceHeight1_adj(m)"], label = 'SonicRanger1')
            
    if "SurfaceHeight2_adj(m)" in df.columns:
        if np.any(~np.isnan(df["SurfaceHeight2_adj(m)"])):
            plt.plot(df["time"], df["SurfaceHeight2_adj(m)"], label = 'SonicRanger2')
            
    plt.legend(prop={'size': 15})
    plt.xlabel('Year',size=20)
    plt.ylabel('Height (m)',size=20)
    plt.title(site,size=20)
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.grid()
    f1.savefig('figures/'+site+'_surface_height.png',dpi=90, bbox_inches='tight')
    return df