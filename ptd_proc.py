# -*- coding: utf-8 -*-

"""

@author: Adrien Wehrlé, Jason E. Box, B. Vandecrux
 GEUS (Geological Survey of Denmark and Greenland)


This code contains 3 functions:
    
    -load_data(): Load a PROMICE station dataset including all years or selected one(s).
    -IA_processing(): Processing, filtering and exclusion of Ice Ablation (IA)  
                      spanning the onset of bare ice conditions.

"""

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import Counter
import math
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

#%%
def load_data(file, year):
    '''
    Loading PROMICE data for a given station and all or given year(s)
    into a DataFrame. 
    
    INTPUTS:
        file: Path to the desired file containing PROMICE data [string]
        year: Year to import. If 'all', all the years are imported [int,string]
    
    OUTPUTS:
        promice_data: Dataframe containing PROMICE data for the desired settings [DataFrame]
    '''
        
    #extract site name
    site=file.split('/')[-1].split('_')[0]+'_'+file.split('/')[-1].split('_')[1]
    
    if site[:3]=='MIT' or site[:3]=='EGP' or site[:3]=='CEN':
        site=site.split('_')[0]
    
    #load data
    promice_data=pd.read_csv(file, delim_whitespace=True)
    
    #set invalid values (-999) to nan 
    promice_data[promice_data==-999.0]=np.nan
    
    if year!='all':
        promice_data=promice_data[promice_data.Year==year]
    elif isinstance(year, list):
        promice_data[promice_data.Year.isin(year)]
    
    if promice_data.empty:
        print('ERROR: Selected year not available')
        return
    return promice_data, site
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
def plot_pres_trans_adj(df, year_list,site, ShowInitial = True):
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
    f1.text(0.02, 0.5, 'Ice ablation (m)', va='center', rotation='vertical', size = 20)
    if ShowInitial:
        tag='_1'
    else:
        tag='_0'
    f1.savefig('figures/'+site+'_DPT_adj'+tag+'.png',dpi=300, bbox_inches='tight')
#%%                   
def DPT_processing(df, year, site, visualisation=True):
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
        plot_pres_trans_adj(df, year_list,site, ShowInitial = True)
        plot_pres_trans_adj(df, year_list,site, ShowInitial = False)
    return df
