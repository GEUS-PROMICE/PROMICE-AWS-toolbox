![PROMICE station](doc/aws.jpg)

# PROMICE-AWS-toolbox

Processing toolbox for PROMICE Automatic Weather Station (AWS) data, and much more.

This repository contains Python functions for quality check, filtering and adjustment of AWS data. They rely on pandas DataFrames and require a physical copy of the PROMICE data (available here: www.promice.dk).


![ptd_proc_KAN_L](doc/fig1.JPG)

All functions are located in the script [PROMICE_lib.py](PROMICE_lib.py) and an exemple of how to use them is given in [main,py](main.py).

## Main functions

1. [remove_flagged_data](#remove_flagged_data)
2. [adjust_data](#adjust_data)
3. [combine_hs_dpt](#combine_hs_dpt)
4. [Output PROMICE_L2 file](#Output-PROMICE_L2-file)
5. [Repporting](#repporting)
6. [Running the scripts](#running)

# remove_flagged_data

[to do: flag instead of remove]

*Illustration:*
![](https://raw.githubusercontent.com/GEUS-PROMICE/PROMICE-AWS-toolbox/master/figures/TAS_A_DepthPressureTransducer_Corm_data_removed.png)

This function reads the station-specific error files [metadata/flags/\<station_name>.csv](metadata/flags) where the erroneous periods are reported for each variable.

These error files have the following structure:

t0 | t1 |  variable | flag | comment | URL_graphic
-- | -- |  -- | -- | -- | -- 
2017-05-23 10:00:00 | 2017-06-10 11:00:00 | DepthPressureTransducer_Cor | CHECKME | manually flagged by bav | https://github.com/GEUS-PROMICE/AWS-data/blob/main/flags/graphics/KPC_L_error_data.png
... | ... |  ... | ... | ... | ...

with

field | meaning
-- | --
*t0* |  ISO date of the begining of flagged period
*t1*| ISO date of the end of flagged period
*variable*|name of the variable to be flagged. [to do: '*' for all variables]
*flag*| short flagging abreviation: <br> - CHECKME<br> - UNKNOWN <br> - NAN <br> - OOL <br> - VISIT
*comment* | Description of the issue
*URL_graphic* | URL to illustration or Github issue thread

The file is comma-separated:
```
t0,t1,variable,flag,comment,URL_graphic
2012-07-19T00:00:00+00:00,2012-07-30T00:00:00+00:00,SnowHeight(m),CHECKME,manually flagged by bav,https://github.com/GEUS-PROMICE/AWS-data/blob/main/flags/graphics/KPC_L_error_data.png
2012-07-19T00:00:00+00:00,2012-07-21T00:00:00+00:00,DepthPressureTransducer_Cor(m),CHECKME,manually flagged by bav,https://github.com/GEUS-PROMICE/AWS-data/blob/main/flags/graphics/KPC_L_error_data.png
...
```

The function [remove_flagged_data](https://github.com/GEUS-PROMICE/PROMICE-AWS-toolbox/blob/c2e86f679a5376b391e2d9b0c524455242a6d72a/PROMICE_lib.py#L82) then removes these flagged data from the dataframe.

## adjust_data
[to do: add more adjustment functions (rotation, smoothing... etc)]

*Illustration:*
![](https://raw.githubusercontent.com/GEUS-PROMICE/PROMICE-AWS-toolbox/master/figures/UPE_L_adj_DepthPressureTransducer_Cor(m).jpeg)

This function reads the station-specific adjustment files [metadata/flag-fix/\<station_name>.csv](metadata/flag-fix) where the required adjustments are reported for each variable.


These error files have the following structure:

t0 | t1 |  variable | adjust_function | adjust_value|comment|URL_graphic
-- | -- |  -- | -- | -- | -- | -- 
2017-05-23 10:00:00 | 2017-06-10 11:00:00 | DepthPressureTransducer_Cor | add | -2 |manually adjusted by bav | https://raw.githubusercontent.com/GEUS-PROMICE/PROMICE-AWS-toolbox/master/figures/UPE_L_adj_DepthPressureTransducer_Cor(m).jpeg
... | ... |  ... | ... | ... | ... | ...

with

field | meaning
-- | --
*t0* |  ISO date of the begining of flagged period
*t1*| ISO date of the end of flagged period
*variable*|name of the variable to be flagged. [to do: '*' for all variables]
*adjust_function*| function that needs to be applied over the given period: <br> - add<br> - filter_min <br> - filter_max <br> - rotate <br> - smooth
*adjust_value* | input value to the adjustment function
*comment* | Description of the issue
*URL_graphic* | URL to illustration or Github issue thread

The file is comma-separated:
```
t0,t1,variable,adjust_function,adjust_value,comment,URL_graphic
2015-03-01T00:00:00+00:00,,DepthPressureTransducer_Cor(m),add,2.3,manually adjusted by bav,https://github.com/GEUS-PROMICE/PROMICE-AWS-toolbox/blob/master/Report_toc.md#s15-2-1
...
```

The function [adjust_data](https://github.com/GEUS-PROMICE/PROMICE-AWS-toolbox/blob/c2e86f679a5376b391e2d9b0c524455242a6d72a/PROMICE_lib.py#L154) then applies the given function to the given variable in the dataframe. **The adjusted variable is named *\<variable_name>_adj* in the final dataframe. The original data is kept.**

## combine_hs_dpt

This is a non-trivial procsessing step combining semi-automatically snow height, surface height and ice surface height measurements into a single record. It is still under development.

It uses 
**SnowHeight(m)** that contains the adjusted and filtered data from the sonic ranger mounted on the AWS
**SurfaceHeight_adj(m)** that contains the adjusted and filtered data from the sonic ranger mounted on the stake assembly
**DepthPressureTransducer_Cor_adj(m)** that contains the adjusted and filtered pressure transducer data

More info will come.

*Illustration:*
![](https://raw.githubusercontent.com/GEUS-PROMICE/PROMICE-AWS-toolbox/master/figures/QAS_U_surface_height.png)



## Running the tools

```python
    import PROMICE_lib as pl
    path_to_PROMICE='path_to_PROMICE'
    site = 'KPC_U'
    df, site =pl.load_data(file=path_to_PROMICE+site+'_hour_v03.txt', year='all')
      
    # processing snow height
    df = pl.hs_proc(df,site, visualisation=True)
```
# Output PROMICE_L2 file

A tab-delimited text file, with same format and same variable names is saved.
The added fields are the variable-specific flag columns and the adjusted varaible columns.

# Reporting

A human-readable data processing report is saved here:
https://github.com/GEUS-PROMICE/PROMICE-AWS-toolbox/blob/master/Report_toc.md


# Running

All these function can be run using the [main.py](main.py) script

```python
    import PROMICE_lib as pl
    import sys
    sys.stdout = open("Report.md", "w")
    
    path_to_PROMICE='path_to_PROMICE'
    site = 'QAS_U'
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
    %run tocgen.py Report.md Report_toc.md
```






