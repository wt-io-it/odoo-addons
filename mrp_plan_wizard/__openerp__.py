# -*- coding: utf-8 -*-
{
    "sequence": 10,
    'name': 'Material Planning Wizard',
    'summary': "Material Planning Wizard for BoM",
    'category': 'Manufacturing',
    "version": "1.0.2",
    'depends': ['mrp'],
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    "contributors": [
        "Wolfgang Taferner (WT-IO-IT GmbH)"
    ],
    'images': ['static/description/main_screenshot.jpg'],
    'data': [
        'views/material_plan_wizard_view.xml',
        'views/report_mrp_plan.xml',
        'report/material_plan_list_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
