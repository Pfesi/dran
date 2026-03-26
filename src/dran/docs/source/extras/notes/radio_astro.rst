.. The radiometer equation page

Radio astronomy basics
======================

Radio telescopes ...

The radiometer equation is 

.. math::
    \sigma_T = \frac{T_{sys}}{\sqrt{\Delta \nu \, t}}




System temperature (Tsys)
-------------------------

In radio astronomy, system temperature (:math:`T_{sys}`) measures the total 
noise power detected by the receiver system. Astronomers express 
it as an equivalent temperature in kelvin [K]. It represents all noise 
sources entering the telescope and receiver signal chain or the sum of 
the noise contributions from the sky, telescope, and receiver electronics.

In practice, we represent the contribution using the equation:


.. math:: 
    T_{sys} = T_{sky} + T_{spill} + T_{ground} + T_{rec} + T_{atm}

Components:
Tant is antenna temperature. Noise entering from the sky and surroundings.
Trec is receiver temperature. Noise generated inside the electronics.
Tsky. Astronomical background emission. Includes the target source, cosmic microwave background, and Galactic emission.
Tatm. Atmospheric emission from water vapor and oxygen.
Tspill. Spillover noise. Radiation entering the feed from outside the main beam.
Tground. Thermal radiation from the ground entering through sidelobes.
Trec. Electronic noise from amplifiers, mixers, cables, and detectors.

.. seealso::
    - Reference: J. D. Kraus. Radio Astronomy. 2nd ed. Cygnus-Quasar Books. 1986. 
    - Reference: T. L. Wilson, K. Rohlfs, S. Hüttemeister. Tools of Radio Astronomy. 6th ed. Springer. 2013.
