TOKEN_ERROR_CODES = {
    '300': {
        'silver_code': 'default',
        'reason': 'The REF_NO specified is not a valid transaction',
    },

    '400': {
        'silver_code': 'default',
        'reason': 'The METHOD variable needs to have one of the following values:TOKEN_NEWSALE, TOKEN_CANCEL, TOKEN_GETINFO',
    },

    '500': {
        'silver_code': 'default',
        'reason': 'The value of TIMESTAMP differs too much from the current time. Check your system clock and ensure that TIMESTAMP is in UTC timezone.',
    },

    '600': {
        'silver_code': 'default',
        'reason': 'Make sure that your MerchantID is the same one found in yourPayU Control Panel',
    },

    '601': {
        'silver_code': 'insufficient_funds',
        'reason': 'The credit card used has insufficient funds available.',
    },

    '602': {
        'silver_code': 'expired_card',
        'reason': 'The credit card used is expired',
    },

    '603': {
        'silver_code': 'default',
        'reason': 'Temporary processing error. Retrying after a few minutes should work.',
    },

    '604': {
        'silver_code': 'invalid_card',
        'reason': 'The credit card used is invalid.',
    },

    '605': {
        'silver_code': 'default',
        'reason': 'General system error. Retrying after a few minutes should work but if it\'s not please contact our support team.',
    },

    '606': {
        'silver_code': 'transaction_declined_by_bank',
        'reason': 'Invalid Transaction error specified by the credit card company.',
    },

    '607': {
        'silver_code': 'default',
        'reason': 'The bank is still processing the transaction, check order status using IOS webservice.',
    },

    '1200': {
        'silver_code': 'default',
        'reason': 'There is a problem with your SIGN variable. Please check your code.',
    },

    '1300': {
        'silver_code': 'default',
        'reason': 'The REF_NO you have specified is not valid. Please check the value.',
    },

    '1500': {
        'silver_code': 'default',
        'reason': 'Invalid Token command for the REF_NO you have specified.',
    },

    '1600': {
        'silver_code': 'default',
        'reason': 'Invalid External Ref No',
    },

    '1900': {
        'silver_code': 'default',
        'reason': 'The AMOUNT value should be a positive number, either integer or a float.',
    },

    '2000': {
        'silver_code': 'default',
        'reason': 'You have exceeded the maximum amount limit for your terminal. Please try again in a few minutes.',
    },

    '2100': {
        'silver_code': 'default',
        'reason': 'CURRENCY variable has an unsupported or invalid value.',
    },

    '2200': {
        'silver_code': 'expired_payment_method',
        'reason': 'Operation was not performed because the token has expired.',
    },

    '2300': {
        'silver_code': 'expired_payment_method',
        'reason': 'Operation was not performed because the token has expired.',
    },

    '2401': {
        'silver_code': 'default',
        'reason': 'BILL_LNAME field is mandatory',
    },

    '2402': {
        'silver_code': 'default',
        'reason': 'BILL_FNAME field is mandatory',
    },

    '2403': {
        'silver_code': 'default',
        'reason': 'BILL_EMAIL field is mandatory',
    },

    '2404': {
        'silver_code': 'default',
        'reason': 'BILL_EMAIL field is not a valid e-mail',
    },

    '2405': {
        'silver_code': 'default',
        'reason': 'BILL_PHONE field is mandatory',
    },

    '2406': {
        'silver_code': 'default',
        'reason': 'BILL_ADDRESS field is mandatory',
    },

    '2407': {
        'silver_code': 'default',
        'reason': 'BILL_CITY field is mandatory',
    },

    '2408': {
        'silver_code': 'default',
        'reason': 'DELIVERY_LNAME field is mandatory',
    },

    '2409': {
        'silver_code': 'default',
        'reason': 'DELIVERY_FNAME field is mandatory',
    },

    '2410': {
        'silver_code': 'default',
        'reason': 'DELIVERY_PHONE field is mandatory',
    },

    '2411': {
        'silver_code': 'default',
        'reason': 'DELIVERY_ADDRESS field is mandatory',
    },

    '2412': {
        'silver_code': 'default',
        'reason': 'DELIVERY_CITY field is mandatory',
    },

    '2413': {
        'silver_code': 'default',
        'reason': 'DELIVERY_EMAIL field is not a valid e-mail',
    },

    '2414': {
        'silver_code': 'default',
        'reason': 'BILL_COUNTRYCODE field is not a valid ISO 3166-1 alpha-2country code',
    },

    '2415': {
        'silver_code': 'default',
        'reason': 'DELIVERY_COUNTRYCODE field is not a valid ISO 3166-1 alpha-2country code',
    },

    '3000': {
        'silver_code': 'default',
        'reason': 'Invalid number of installments selected',
    },

    '3100': {
        'silver_code': 'default',
        'reason': 'Token is already persistent',
    },

    '3101': {
        'silver_code': 'expired_payment_method',
        'reason': 'Token has expired',
    },

    '3200': {
        'silver_code': 'default',
        'reason': 'Token usage on marketplace orders is restricted on this protocol',
    },

    '4000': {
        'silver_code': 'default',
        'reason': 'Please check if the card scheme used to make the original transaction is still enabled for that merchant.',
    },
}

ALU_ERROR_CODES = {
    "ALREADY_AUTHORIZED": {
        "silver_code": "default",
        "reason": "Tried to place a new order with the same ORDER_REF and HASH as previous one."
    },
    "AUTHORIZATION_FAILED": {
        "silver_code": "default",
        "reason": "The payment was not authorized."
    },
    "INVALID_CUSTOMER_INFO": {
        "silver_code": "default",
        "reason": "Required data from the Shopper is missing or is malformed."
    },
    "INVALID_PAYMENT_INFO": {
        "silver_code": "default",
        "reason": "Card data is not correct."
    },
    "INVALID_ACCOUNT": {
        "silver_code": "default",
        "reason": "The Merchant name is not correct."
    },
    "INVALID_PAYMENT_METHOD_CODE": {
        "silver_code": "default",
        "reason": "Payment method code is NOT recognized."
    },
    "INVALID_CURRENCY": {
        "silver_code": "default",
        "reason": "Payment currency is not recognized."
    },
    "REQUEST_EXPIRED": {
        "silver_code": "default",
        "reason": "The request has expired based on provided ORDER_DATE."
    },
    "HASH_MISMATCH": {
        "silver_code": "default",
        "reason": "Hash sent by the Merchant does not match the hash calculated by PayU."
    },
    "WRONG_VERSION": {
        "silver_code": "default",
        "reason": "ALU version sent by the Merchant does not exist."
    },
    "INVALID_CC_TOKEN": {
        "silver_code": "default",
        "reason": "CC_TOKEN sent by the Merchant is not valid."
    },
}
