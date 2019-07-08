# -*- encoding: utf-8 -*-
{
    "name": "Partner List Custom Sort",

    "version": "1.0",
    "sequence": 15,
    "author": "WT-IO-IT GmbH",
    "website": "https://www.wt-io-it.at",

    "category": "Website",

    'summary': "Enable sorting partners in website partner list",
    'license': 'AGPL-3',
    "description": """

Enables manually sorting the partners withing a grad / level
======================================================================

In detail the module
 * allows to set a custom implemented_count for partners that should be ranked higher
""",

    "depends": [
        'website_crm_partner_assign',
    ],
    "demo": [],

    "data": [
        'views/res_partner_views.xml',
    ],

    "certificate": '',
    "application": False,
}
