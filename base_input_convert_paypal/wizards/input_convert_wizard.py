# -*- coding: utf-8 -*-
import datetime
import sys
import itertools
import base64
import csv
import copy
from decimal import Decimal

PY2 = sys.version_info[0] == 2
if PY2:
    from io import BytesIO as StringIO
else:
    from io import StringIO

from odoo import models, fields, api, _
from odoo.tools.misc import ustr
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class InputConvertWizard(models.TransientModel):
    _inherit = 'input.convert.wizard'

    conversion_type = fields.Selection(
        string='Conversion Type',
        selection_add=[
            ('paypal', 'PayPal')
        ]
    )

    def _paypal_convert_input_method(self, atts, options=None):
        output_vals = {}
        if atts.mimetype == 'text/csv':
            options = options or {}
            csv_data = base64.b64decode(atts.datas)
            if not PY2:
                csv_data = ustr(csv_data)
            dialect = csv.Sniffer().sniff(csv_data)
            dialect.lineterminator = '\n'

            encoding = options.get('encoding', 'utf-8')
            if encoding != 'utf-8':
                csv_data = csv_data.decode(encoding).encode('utf-8')
                
            fieldnames = [
                "date", "Uhrzeit", "Zeitzone", "note", "currency_id", "amount",
                "Gebühr", "Netto", "Guthaben", "name", "DO NOT IMPORT", "partner_name",
                "Name der Bank", "DO NOT IMPORT", "Versand- und Bearbeitungsgebühr",
                "Umsatzsteuer", "Rechnungsnummer", "ref"
            ]
            paypal_dict = csv.DictReader(StringIO(csv_data), fieldnames=fieldnames, dialect=dialect)
            paypal = {}
            fees = {}
            dates = {}
            fieldnames_new = fieldnames[:]
            fieldnames_new.insert(0, 'id')
            all_dates = []
            for row in itertools.islice(paypal_dict, 1, None):
                try:
                    key = row['currency_id']
                    if key not in paypal:
                        paypal[key] = []
                        fees[key] = []
                        dates[key] = []
                    fee = Decimal(row['Gebühr'].replace(',', ''))
                    date_v = datetime.datetime.strptime(row['date'], '%m/%d/%Y')
                    date = date_v.strftime('%Y-%m-%d')
                    amount = Decimal(row['amount'].replace(',', ''))
                except Exception as e:
                    raise UserError('It seems that you have chosen a wrong file or a wrong conversion type!\n\n%s' % (e))

                direction = 'pos'
                if amount < 0:
                    direction = 'neg'
                row['id'] = 'txn_%s_%s%s%s_%s' % (row['name'], date_v.year, date_v.month, date_v.day, direction)
                row['date'] = date
                row['amount'] = amount
                row['Gebühr'] = fee

                fees[key].append(fee)
                dates[key].append(date)
                all_dates.append(date)
                paypal[key].append(row)

            # Min/Max date from all dates
            min_date = min(all_dates)
            max_date = max(all_dates)

            for key in paypal.keys():
                if not dates[key]:
                    continue
                if sum(fees[key]) != 0:
                    fee_vals = dict(id='txn_fees_paypal_%s_%s%s' % (key.lower(), min_date.replace('-', ''), max_date.replace('-', '')), date=max_date, name='PayPal Gebühren %s - %s (%s)' % (min_date.replace('-', ' '), max_date[-2:], key), amount=sum(fees[key]), currency_id=key, ref='Automatische Berechnung (Transaktionen)', note='')
                    paypal[key].append(fee_vals)

            for currency, lines in paypal.items():
                if len(lines) == 0:
                    continue
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames_new, dialect=dialect)
                writer.writeheader()
                for line in lines:
                    writer.writerow(line)
                filename = '%s - %s (%s) - PayPal Import (Odoo).csv' % (min_date.replace('-', ' '), max_date[-2:], currency)
                output_vals[filename] = output  # output.getvalue().strip('\n')
                _logger.info('File %s with %s lines to be created', currency, len(lines))
        return output_vals

