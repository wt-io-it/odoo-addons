# -*- coding: utf-8 -*-
{
    'name': 'Website Sale Variant Description',
    'summary': "Website Sale Variant Description",
    'category': 'Sale',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'description': """
    """,
    'depends': [
        'website_sale_stock',
        'sale_description_variant',
    ],
    'data': [
        'views/header.xml',
        'views/templates.xml',
    ],
    'js': [],
    'css': [
    ],
    'qweb': [],
    'test': [],
    'external_dependencies': {
        'python': [],
    },

    'installable': True,
}
