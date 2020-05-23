# -*- coding: utf-8 -*-
{
    'name': 'Base Preload Compare',
    'summary': "Custom",
    'category': 'Custom',
    "version": "1.0",
    "sequence": 10,
    "author": "woom GmbH, Radu Vecerdea, WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'description': """
        Mark modules and models that are upgraded by a module to be checked for changes before reloading/writing them.
    """,
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/data_preload.xml',
        'data/menu.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [],
    },
    'installable': True,
}
