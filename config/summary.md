---
title: SWF summary report of {day}-{Month}-{year}

---
#### Solar flare: Peak at {flare_peaktime} UT / {fl_goescls}-class
#### SWF event:  {swf_starttime} - {swf_endtime} UT / {local} SLT (central Kansas) / Intensity: {score_desc}

> A summary of flare impacts on SuperDARN HF radar observations in the North American sector with an emphasis on ShortWave Fadeout (SWF).

> Refer [(VT SuperDARN Website)](http://vt.superdarn.org/) for the dataset used in this analysis.

> Methodolgy is described in our SWF characterization paper [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).

> Analysis `.py` files are stored in this repository, also in [(GitHub)](https://github.com/shibaji7/SD_RT_SWF_Monitoring).

## Analysis Summary

> Summary report of GOES X-Ray irradiance. Flare class and peak time is identified in the Soft X-ray sepctrum (SXR, red).

> Summary report of a sub-network of SuperDARN radar chain distributed across the middle and high-latitudes of the North American Sector. SWF phase timings [onset, blackout, recovery start, and end] and phase durations [onset, backout, and recovery] are estimated from the backscatter count `<E>` parameter. Thresholds and alogorithm is defined in [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).


```{python, echo=False}
import contextlib
import os
devnull = open(os.devnull, 'w')
contextlib.redirect_stdout(devnull)

import warnings
warnings.filterwarnings('ignore')
%matplotlib inline
import sys
sys.path.extend(["py/", "py/geo/"])
import datetime as dt
import matplotlib
matplotlib.style.use(["science", "ieee"])
import matplotlib.pyplot as plt
pd.options.display.max_rows = 10
from goes import FlareTS
from fetchUtils import SDAnalysis;
from IPython.display import display, Markdown;

stime, etime = [
    dt.datetime({syear},{smonth},{sday},{shour},{smin}), 
    dt.datetime({eyear},{emonth},{eday},{ehour},{emin})
]
rads = [{rads}]

g = FlareTS([stime, etime])
_ = g.plot_TS([stime, etime])


sd = SDAnalysis(dates=[stime, etime], rads=rads);
_= sd.plot_summary_TS()
```

