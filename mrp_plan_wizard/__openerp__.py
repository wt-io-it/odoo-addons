# -*- coding: utf-8 -*-
{
    'name': 'Material Planning Wizard',
    'summary': "Material Planning Wizard for BoM",
    'category': 'Manufacturing',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH",
    "contributors": [
        "Wolfgang Taferner (WT-IO-IT GmbH)"
    ],
    "website": "https://www.wt-io-it.at",
    'depends': ['mrp'],
    'data': [
        'views/material_plan_wizard_view.xml',
        'views/report_mrp_plan.xml',
        'report/material_plan_list_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
