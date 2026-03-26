Weather calibration
===================


Water vapor
-----------

# calculate PWV values - copy from Mikes drift_fits2asc_HINDv16.c file


Precipitable water vapour (pwv), if it fails we set everything to 1 - why ?

rh_percent = relative humidity

pwv_mm = max(0.0, 4.39 * rh_percent / 100.0 / temp_k * math.exp(26.23 - 5416.0 / temp_k))
    
svp_kpa = 0.611 * math.exp(17.27 * (temp_k - 273.13) / (temp_k - 273.13 + 237.3))
    
avp_kpa = svp_kpa * rh_percent / 100.0
    
dpt_k = (116.9 + 237.3 * math.log(avp_kpa)) / (16.78 - math.log(avp_kpa)) if avp_kpa > 0 else np.nan
        
wvd_g_m3 = max(0.0, 2164.0 * avp_kpa / temp_k)


At 4.5 cm 
----------

Maser Freq, no calibration at the moment

At 2GHz
-------

atmosabs = math.exp(0.005 / math.cos(np.deg2rad(za_deg)))


At 12 GHz
---------

We calculate atmospheric depth or opacity

tau10 = 0.0071 + 0.00021 * pwv

tau15 = (0.055 + 0.004 * wvd) / 4.343

tbatmos10 = 260.0 * (1.0 - math.exp(-tau10))

tbatmos15 = 260.0 * (1.0 - math.exp(-tau15))


Also calculate tme mean atmospheric correction - why ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
I think its because we do't have 12 GHz opacity correction

za_rad = np.deg2rad(za_deg)

mean_atm = math.exp((tau15 + tau10) / 2.0 / math.cos(za_rad))


At 22 GHz
----------

tau221 = 0.0140 + 0.00780 * pwv
        
tau2223 = (0.110 + 0.048 * wvd) / 4.343
        
tbatmos221 = 260.0 * (1.0 - math.exp(-tau221))

tbatmos2223 = 260.0 * (1.0 - math.exp(-tau2223))


Calibrating jupiter
~~~~~~~~~~~~~~~~~~~



At 8.4 GHz
----------

za_rad = np.deg2rad(za_deg)

sec_z = 1.0 / math.cos(za_rad) # 1.0 / np.cos(za  * dtr)

x_z = (-0.0045 + 1.00672 * sec_z - 0.002234 * sec_z**2 - 0.0006247 * sec_z**3)

dry_atmos_transmission = 1.0 / math.exp(0.0069 * (1.0 / math.sin((90.0 - za_deg) * DEG_TO_RAD) - 1.0))

zenith_tau_at_1400m = 0.00610 + 0.00018 * pwv

abs_at_zenith = math.exp(zenith_tau_at_1400m * x_z)
