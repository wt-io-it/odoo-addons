# -*- coding: utf-8 -*-
{
    'name': 'Account Invoice Approval',
    'summary': "Account Invoice Approval",
    'category': 'Accounting',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}
