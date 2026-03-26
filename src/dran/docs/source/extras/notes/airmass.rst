.. The airmass page

Airmass
=======

They come from the observation table columns in your monitoring DB, in this order:

SEC_Z (used directly as airmass)
If SEC_Z is missing, from ZA using
airmass = 1 / cos(ZA in radians)
