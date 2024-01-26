# Solar Flare & SWF Monitoring

> The X-ray, Extreme Ultra Violate (EUV) radiation released during a solar X-ray flare induces electron density enhancement in the dayside D-region ionosphere[^1]. This heightened electron density has the capacity to elevate absorption in the high frequency (HF:3-30 MHz) range, specifically between 3 and 30 MHz. The consequence is a reduction in signal strength, affecting shortwave radio transmissions, commonly known as shortwave fadeout, SWF.

> This monitoring tool provides a summary of flare impacts on SuperDARN HF radar observations in the North American sector with an emphasis on ShortWave Fadeout (SWF). Specifically, tool provides the following data/analysis products:
> * *Event-based Summary Reports*: Pre-loaded events by [calender](flarelist.html), shwoing solar irradiance (at X-ray band) condition and associated ionospheric/HF response recoreded by SuperDARN.
> * *New HF absorption model*: Pre-loaded modeled events by [calender](newdrap.html), shwoing solar irradiance (at X-ray band) condition and modeled HF condition during the peak of the flare.

### Event-based Summary Reports

> Summary report of GOES X-Ray irradiance. Flare class and peak time is identified in the Soft X-ray sepctrum (SXR, red). Summary report of a sub-network of SuperDARN radar chain distributed across the middle and high-latitudes of the North American Sector. SWF phase timings [onset, blackout, recovery start, and end] and phase durations [onset, backout, and recovery] are estimated from the backscatter count `<E>` parameter. Thresholds and alogorithm is defined in Chakraborty et al. (2018)[^2]. Please find example event and parameter description in this [webpage]().

### New HF Absorption-Model:

> Latest study by Fiori et al. (2022)[^3] optimized a simple absorption model using data from solar X-ray flares and riometer stations across Canada. In a specific event study, our optimized model showed a 1% overestimation of absorption during an X2.1 solar X-ray flare, correcting an underestimation by the NOAA D-region Absorption Prediction (D-RAP) model. In a broader statistical study involving 87 events, event-by-event optimization demonstrated excellent agreement between measured and modeled data, with a Pearson correlation coefficient (R) of 0.88 and a slope (m) of 0.91. The study also developed a generalized model using data from all events, showing slightly reduced correlation (R = 0.75) and slope (m = 0.80). The model's accuracy, evaluated by prediction efficiency, peaked at 0.78 for event-by-event analysis and 0.48 for the collective dataset. This new HF absorption model is also presented along with DRAP[^4] [^5] [^6] [^7] model output. Please find example event and parameter description in this [webpage]().


#### Acknowledgements:
We acknowledge the use of SuperDARN data. SuperDARN is a network of radars funded by national scientific funding agencies of Australia, Canada, China, France, Italy, Japan, Norway, South Africa, the United Kingdom, and the United States of America. We wish to acknowledge the use of the NOAA/GOES X-ray [dataset](https://www.ngdc.noaa.gov/stp/satellite/goes-r.html) for flare confirmation and dataset. This work is funded by the Aeronautics and Space Administration grant `80NSSC20K1380`.

#### Open Science:
Refer VT SuperDARN [Website](https://vt.superdarn.org/) for the dataset used in this analysis. Methodolgy is described in our SWF characterization paper (Chakraborty et al. 2018[^2]). Analysis `.py` files are stored in [GitHub](https://github.com/shibaji7/SD_RT_SWF_Monitoring).

#### References:
[^1]: Davies, K., Ionospheric Radio. Peregrinus Ltd., London, UK. 1990.

[^2]: Chakraborty, S., Ruohoniemi, J. M., Baker, J. B. H., & Nishitani, N. (2018). Characterization of short-wave fadeout seen in daytime SuperDARN ground scatter observations. Radio Science, 53, 472–484. https://doi.org/10.1002/2017RS006488

[^3]: R.A.D. Fiori, S. Chakraborty, L. Nikitina, Data-based optimization of a simple shortwave fadeout absorption model, Journal of Atmospheric and Solar-Terrestrial Physics,
Volume 230, 2022, 105843, ISSN 1364-6826, https://doi.org/10.1016/j.jastp.2022.105843.

[^4]: Sauer, H. H., and D. C. Wilkinson, A Global Space Weather Model of Ionospheric HF/VHF Radio-Wave Absorption due to Solar Energetic Protons,Space Weather, submitted, 2008.

[^5]: Space Environmental Forecaster Operations Manual, page 4.3.1, 55th Space Weather Squadron, Falcon AFB, USAF, 21 October 1997.

[^6]: Stonehocker, G. H., Advanced Telecommunication Forecasting Technique, in Ionospheric Forecasting, AGARD CONF. Proc. No. 49, Advisory Group for Aerospace Research and Development, NATO; Agy, V. (Ed), p27-1, 1970.

[^7]: NOAA, SWPC, Global D-Region Absorption Prediction, https://www.swpc.noaa.gov/content/global-d-region-absorption-prediction-documentation
