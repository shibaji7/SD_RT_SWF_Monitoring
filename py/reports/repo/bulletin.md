---
title: SuperDARN Flare Bulletin for solar flare event of {day}-{Month}-{year}
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


edate = dt.datetime({year},{month},{day},{hour},{minute})
rads = [{rads}]
stime, etime = [dt.datetime({year},{month},{day},{shour}), 
            dt.datetime({year},{month},{day},{ehour})]

_ = FanPlots().plot_fov(edate, rads)
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

gx = goes.GOES().load_data().analyze_flare().plot_TS([stime, etime])
ptime, cls = gx.id_c, gx.c
```

> Summary report of a sub-network of SuperDARN radar chain distributed across the middle and high-latitudes of the North American Sector. SWF phase timings [onset, blackout, recovery start, and end] and phase durations [onset, backout, and recovery] are estimated from the backscatter count `<E>` parameter. Thresholds and alogorithm is defined in [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).


> $3\times 3$ FoV plot showing overall progression of SWF.
```{python, echo=False}
create3X3summaryplot([stime, edate, etime], rads)
```

> $3\times 1$ RTI plot showing overall progression of SWF along beam 7 of the radars.

```{python, echo=False}
import sdc
from IPython.display import display, Markdown

sd = sdc.SDAnalysis(dates=[stime, etime], rads=rads)
_ = sd.plot_TS(7)
```