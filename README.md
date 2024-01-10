# Solar Flare & SWF Monitoring

> The electromagnetic radiation released during a solar X-ray flare induces electron density enhancement in the dayside D-region ionosphere. This heightened electron density has the capacity to elevate absorption in the high frequency (HF) range, specifically between 3 and 30 MHz. The consequence is a reduction in signal strength, affecting shortwave radio transmissions, commonly known as shortwave fadeout.

> A summary of flare impacts on SuperDARN HF radar observations in the North American sector with an emphasis on ShortWave Fadeout (SWF).

> Refer [(VT SuperDARN Website)](http://vt.superdarn.org/) for the dataset used in this analysis.

> Methodolgy is described in our SWF characterization paper [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).

> Analysis `.py` files are stored in this repository, also in [(GitHub)](https://github.com/shibaji7/SD_RT_SWF_Monitoring).

### Analysis Summary

> Summary report of GOES X-Ray irradiance. Flare class and peak time is identified in the Soft X-ray sepctrum (SXR, red).

> Summary report of a sub-network of SuperDARN radar chain distributed across the middle and high-latitudes of the North American Sector. SWF phase timings [onset, blackout, recovery start, and end] and phase durations [onset, backout, and recovery] are estimated from the backscatter count `<E>` parameter. Thresholds and alogorithm is defined in [(Chakraborty et al. 2018)](https://doi.org/10.1002/2017RS006488).

### New DRAP-Model

> Latest study by Fiori et al.([2022](https://www.sciencedirect.com/science/article/pii/S1364682622000190)) optimized a simple absorption model using data from solar X-ray flares and riometer stations across Canada. In a specific event study, our optimized model showed a 1% overestimation of absorption during an X2.1 solar X-ray flare, correcting an underestimation by the NOAA D-region Absorption Prediction (D-RAP) model. In a broader statistical study involving 87 events, our event-by-event optimization demonstrated excellent agreement between measured and modeled data, with a Pearson correlation coefficient (R) of 0.88 and a slope (m) of 0.91. We also developed a generalized model using data from all events, showing slightly reduced correlation (R = 0.75) and slope (m = 0.80). The model's accuracy, evaluated by prediction efficiency, peaked at 0.78 for event-by-event analysis and 0.48 for the collective dataset. This study underscores the benefits of data-based optimization in modeling absorption during shortwave fadeout.