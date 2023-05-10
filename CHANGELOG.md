# Changelog


## Unrealeased changes
_Nothing yet_


## 0.6.1 (2023-05-10)
- Always save request for transactions


## 0.6.0 (2023-05-10)
- Require django-payu-ro==1.5.0
- Use black to format code
- Save request and result data for failed transactions


## 0.5.1 (2022-01-05)
- Require django-payu-ro==1.4.2


## 0.5.0 (2021-06-28)
- Require Python==3.7, Django>3.1,<3.3, django-silver>=0.11 and django-payu-ro==1.4.1. **(BREAKING)**


## 0.4.1 (2021-02-05)
- Fixed modifying 3DS data for already verified or canceled payment methods.


## 0.4.0 (2020-12-22)
- Added support for ALU v3 (to comply with 3DS2.0), while removing the old ALU method. **(BREAKING)**
