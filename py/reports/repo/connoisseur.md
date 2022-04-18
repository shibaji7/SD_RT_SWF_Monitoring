---
title: SuperDARN Flare Bulletin for solar flare event of 11-March-2015
author: Chakraborty, S.

---

> A summary of flare impacts on SuperDARN HF radar observations in the North American sector with an emphasis on ShortWave Fadeout (SWF).

> Refer [(VT SuperDARN Website)](http://vt.superdarn.org/) for the dataset used in this analysis.

> Methodolgy is described in our SWF characterization paper [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).

> Analysis `.py` files are stored in this repository, also in [(GitHub)](https://github.com/shibaji7/SD_RT_SWF_Monitoring).

## Radar Sub-Network

> Sub-network of radars used in this report
```{python, echo=False}
%matplotlib inline
import warnings
warnings.filterwarnings("ignore")
import datetime as dt
import matplotlib
matplotlib.style.use(["science", "ieee"])
import sys, os
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

from sdcarto import *

_ = FanPlots().plot_fov(dt.datetime(2015,3,11,16,20), ['bks','fhe','fhw'])
```

## Analysis Report

> Summary report of GOES X-Ray irradiance. Flare class and peak time is identified in the Soft X-ray sepctrum (SXR, red).

```{python, echo=False}
%matplotlib inline

import datetime as dt
import matplotlib
matplotlib.style.use(["science", "ieee"])
import matplotlib.pyplot as plt
pd.options.display.max_rows = 10

import goes

gx = goes.GOES().load_data().analyze_flare().plot_TS([dt.datetime(2015,3,11,16), dt.datetime(2015,3,11,17)])
ptime, cls = gx.id_c, gx.c
```

```{python, echo=False} 
print(f"We found an {cls}-class flare on {ptime.strftime('%H:%M UT %d %b %Y')}.")
```

> Summary report of a sub-network of SuperDARN radar chain distributed across the middle and high-latitudes of the North American Sector. SWF phase timings [onset, blackout, recovery start, and end] and phase durations [onset, backout, and recovery] are estimated from the backscatter count `<E>` parameter. Thresholds and alogorithm is defined in [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).


[comment]: # ```{python, echo=False}
[comment]: # import sdc
[comment]: # from IPython.display import display, Markdown

[comment]: # sd = sdc.SDAnalysis().fetch_parameters()
[comment]: # display(Markdown(sd.parames.to_markdown()))
[comment]: # _ = sd.plot_TS()
[comment]: # ```

## Definitions:
1. <ins>Solar Flare</ins> is a sudden intensification of solar brightness (specifically in the X–ray and EUV spectrum).
2. <ins>Sudden Ionospheric Disturbance (SID)</ins> is sudden enhancement of plasma density in the dayside ionosphere.
3. <ins>Shortwave Fadeout (SWF)</ins> is sudden increase in Radio-Wave Absorption in high frequency (HF) ranges (3-30 MHz).
4. <ins>Sudden Frequency Deviation (SFD)</ins> is sudden change in Frequency of the traveling Radiowave or `Doppler Flash`.