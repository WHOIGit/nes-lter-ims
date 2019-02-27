import numpy as np

def ts_corrected_nitrate(cal_temp, wl, eno3, eswa, di, dark_value, degc,
                         psu, data_in, frame_type, wllower=217., wlupper=240.):
    """
    Description:

        This Python code is based on Matlab code (NUTNR_Example_MATLAB_Code_20140521_ver_1_00.m) that was developed
        by O.E. Kawka (UW/RSN).

        The code below calculates the Dissolved Nitrate Concentration with the Sakamoto et. al. (2009) algorithm that
        uses the observed sample salinity and temperature to subtract the bromide component of the overall seawater
        UV absorption spectrum before solving for the nitrate concentration.

        The output represent the OOI L2 Dissolved Nitrate Concentration, Temperature and Salinity Corrected (NITRTSC).

    Implemented by:

        2014-05-22: Craig Risien. Initial Code
        2014-05-27: Craig Risien. This function now looks for the light vs dark frame measurements and only calculates
                    nitrate concentration based on the light frame measurements.
        2015-04-09: Russell Desiderio. CI is now implementing cal coeffs by tiling in time, requiring coding changes.
                    The tiling includes the wllower and wlupper variables when supplied by CI.
        2017-06-23  Christopher Wingard. Removed provisioning for CI tiling and vectorized code.

    Usage:

        nitrate = ts_corrected_nitrate(cal_temp, wl, eno3, eswa, di, dark_value, degc, psu, data_in, frame_type,
                                       wllower, wlupper)

            where

        nitrate = L2 Dissolved Nitrate Concentration, Temperature and Corrected (NITRTSC) [uM]

            and

        cal_temp = Calibration water temperature value [deg C]
        wl = (256,) array of wavelength bins
        eno3 = (256,) array of wavelength-dependent nitrate extinction coefficients
        eswa = (256,) array of seawater extinction coefficients
        di = (256,) array of deionized water reference spectrum
        dark_value = (N,) array of dark average scalar value
        degc = (N,) array of water temperature values from co-located CTD [deg C]
        psu = (N,) array of practical salinity values from co-located CTD [unitless].
        data_in = (N x 256) array of raw nitrate measurement values from the UV absorption spectrum data product
            (L0 NITROPT) [unitless]
        frame_type = (N,) array of Frame type, either a light or dark measurement. This function only uses the data
            from light frame measurements, returning a NaN for dark frame measurements
        wllower = Lower wavelength limit for spectra fit. From DPS: 217 nm (1-cm pathlength probe tip) or 220 nm
            (4-cm pathlength probe tip)
        wlupper = Upper wavelength limit for spectra fit. From DPS: 240 nm (1-cm pathlength probe tip) or 245 nm
            (4-cm pathlength probe tip)

    References:

        OOI (2014). Data Product Specification for NUTNR Data Products.
            Document Control Number 1341-00620.
            https://alfresco.oceanobservatories.org/ (See: Company Home >>
            OOI >> Cyberinfrastructure >> Data Product Specifications >>
            1341-00620_Data_Product_Spec_NUTNR_OOI.pdf)
        Johnson, K. S., and L. J. Coletti. 2002. In situ ultraviolet
            spectrophotometry for high resolution and long-term monitoring
            of nitrate, bromide and bisulfide in the ocean. Deep-Sea Res.
            I 49:1291-1305
        Sakamoto, C.M., K.S. Johnson, and L.J. Coletti (2009). Improved
            algorithm for the computation of nitrate concentrations in
            seawater using an in situ ultraviolet spectrophotometer.
            Limnology and Oceanography: Methods 7: 132-143
    """
    # Broadcast inputs to numpy arrays, where needed
    wl = np.atleast_2d(wl)
    eno3 = np.atleast_2d(eno3)
    eswa = np.atleast_2d(eswa)
    di = np.atleast_2d(di)
    dark_value = np.atleast_2d(dark_value)
    degc = np.atleast_2d(degc)
    psu = np.atleast_2d(psu)
    data_in = np.atleast_2d(data_in)
    frame_type = np.atleast_2d(frame_type)

    # Find wavelength bins that fall between the upper and lower limits for spectra fit
    index = np.logical_and(wl >= wllower, wl <= wlupper)

    # subset data so that we only use wavelengths between wllower & wlupper
    wl = wl[index]
    eno3 = eno3[index]
    eswa = eswa[index]
    di = di[index]
    raw = data_in[:, index[0, :]]

    # coefficients to equation 4 of Sakamoto et al 2009 that give the absorbance of seawater at a salinity of 35 psu
    # versus temperature
    asak = 1.1500276
    bsak = 0.02840
    csak = -0.3101349
    dsak = 0.001222

    # create a mask for the dark arrays and generate a default nitrate array set to NaN
    light = np.where((frame_type == 'SLB') | (frame_type == 'SLF') | (frame_type == 'NLF'))[1]
    nitrate = np.ones(raw.shape[0]) * np.nan

    # correct each raw intensity for dark current, using only light frames
    raw_corr = raw[light, :] - dark_value.T[light]

    # calculate absorbance from the corrected intensity data
    absorb = np.log10(di / raw_corr)

    # now estimate molar absorptivity of seawater at in situ temperatures using Satlantic calibration corrections as in
    # Sakamoto et al. 2009.
    molar = (eswa * ((asak + bsak * degc.T[light]) / (asak + bsak * cal_temp)) *
             np.exp(dsak * (degc.T[light] - cal_temp) * (wl.T - 210.0)))
    
    # adjust molar absorptivity for seawater
    molar_psu = psu.T[light] * molar

    # subtract seawater molar absorptivity from the measured absorbance
    absorb_psu = (absorb - molar_psu).T

    # construct an array of eno3, a linear baseline and the wavelengths used for the final calculation
    subset_array_size = np.shape(eno3)
    ones = np.ones(subset_array_size[0]) / 100  # for the constant, linear baseline
    m = np.vstack((eno3, ones, wl / 1000)).T

    # c has NO3, baseline constant, and slope (vs. wavelength)
    c = np.dot(np.linalg.pinv(m), absorb_psu)
    nitrate[light] = c[0, :]   # extract and keep the nitrate calculation for the light frames

    return nitrate
