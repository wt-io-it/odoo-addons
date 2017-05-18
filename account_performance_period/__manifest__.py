# -*- coding: utf-8 -*-
{
    'name': 'Accounting Performance period',
    'summary': "Accounting Performance period",
    'category': 'Accounting',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': [
        'account',
        'date_range',  # OCA/server-tools
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_analytic.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False,
}
