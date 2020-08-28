# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %(username)s

tip list:
    %matplotlib inline
    %matplotlib qt
    import pdb; pdb.set_trace()
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import math
import sys
import datetime
sys.path.append('metadata')

#%%
def hampel(vals_orig, k=7, t0=3):
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
    vals[outlier_idx]=np.nan
    return(vals)

    
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
def firstNonNan(listfloats):
  for item in listfloats:
    if math.isnan(item) == False:
      return item
  
#%%
def plot_hs_adj(df, year_list, site,  
                var1 = "SurfaceHeight1_adj(m)", var2 = "SurfaceHeight1(m)"):
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
            if var=="SurfaceHeight1_adj(m)":
                adj_start = adj_start_1
            elif var == "SurfaceHeight2_adj(m)":
                adj_start = adj_start_2
            else:
                adj_start = [np.nan]
            
            if np.any(~np.isnan(adj_start)):
                for d in adj_start:
                    ax[i,j].axvspan(d-2, d+2, color='orange', alpha=0.5, label='Adjustment')
        ax[i,j].set_xlim((0,365))
        if k == 0:
            ax[i,j].legend(loc='upper right')
        ax[i,j].annotate(str(y),
            xy=(0.05, 0.1), xycoords='axes fraction',size = 15)
    f1.text(0.5, 0.95, site, va='center',  size = 20)
    f1.text(0.02, 0.5, 'Ice ablation (m)', va='center', rotation='vertical', size = 20)

    f1.savefig('figures/hs/'+site+'_DPT_adj'+var1+'.png',dpi=300, bbox_inches='tight')
    
#%%
def hs_proc(df, site, visualisation=True):
    year_list = np.unique(df.Year)

    df["SurfaceHeight1(m)"] = 2.6 - df["HeightSensorBoom(m)"] 
    df["SurfaceHeight2(m)"] = 1 - df["HeightStakes(m)"] 

    z1 = df["SurfaceHeight1(m)"].copy()
    z2 = df["SurfaceHeight2(m)"].copy()
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
        return
    
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
    df["SurfaceHeight1_adj(m)"]=z1.values

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
    df["SurfaceHeight2_adj(m)"]=z2.values

    if visualisation:
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SurfaceHeight1(m)", var2 = "SurfaceHeight1_adj(m)")
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SurfaceHeight2(m)", var2 = "SurfaceHeight2_adj(m)")
        plot_hs_adj(df, year_list = year_list, site=site, 
                    var1 = "SurfaceHeight1_adj(m)", var2 = "SurfaceHeight2_adj(m)")
    return df