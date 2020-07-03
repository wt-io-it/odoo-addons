# -*- coding: utf-8 -*-
import datetime
import sys
import itertools
import base64
import csv
import copy
from decimal import Decimal
from pytz import timezone

PY2=sys.version_info[0] == 2
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
            ('stripe', 'Stripe')
        ]
    )

    @api.multi
    def _stripe_convert_input_method(self, atts, options=None):
        output_vals = {}
        if atts.mimetype == 'text/csv':
            options = options or {}
            csv_data = base64.b64decode(atts.datas)
            if not PY2:
                csv_data = ustr(csv_data)
            dialect = csv.Sniffer().sniff(csv_data)
            dialect.lineterminator = '\n'

            # TODO: guess encoding with chardet? Or https://github.com/aadsm/jschardet
            encoding = options.get('encoding', 'utf-8')
            if encoding != 'utf-8':
                # csv module expect utf-8, see http://docs.python.org/2/library/csv.html
                csv_data = csv_data.decode(encoding).encode('utf-8')
            fieldnames = [
                "id", "Type", "name", "amount", "Fee", "Destination Platform Fee",
                "Net", "DO NOT IMPORT", "date", "Available On (UTC)", "note",
                "amount_currency", "currency_id", "Transfer", "Transfer Date (UTC)",
                "Transfer Group", "DO NOT IMPORT", "ref", "DO NOT IMPORT", "DO NOT IMPORT", "DO NOT IMPORT"
            ]
            stripe_dict = csv.DictReader(StringIO(csv_data), fieldnames=fieldnames, dialect=dialect)
            stripe = {
                'EUR': []
            }
            fees = copy.deepcopy(stripe)
            dates = copy.deepcopy(stripe)
            all_dates = []
            for row in itertools.islice(stripe_dict, 1, None):
                try:
                    key = row['currency_id'].upper()
                    fee = Decimal(row['Fee'].replace(',', '.'))
                    dt = datetime.datetime.strptime(row['date'], '%Y-%m-%d %H:%M')
                    dt_fmt = ['%Y', '%m', '%d', '%H', '%M']
                    dt_vals = tuple(map(lambda fmt: int(datetime.datetime.strftime(dt, fmt)), dt_fmt))
                    date = datetime.datetime(*dt_vals, tzinfo=timezone('UTC')).astimezone(timezone(self.env.user.tz or 'UTC')).strftime('%Y-%m-%d')
                    amount = float(row['amount'].replace(',', '.'))
                    amount_currency = 0
                    if row['amount_currency']:
                        amount_currency = float(row['amount_currency'].replace(',', '.'))
                except Exception as e:
                    raise UserError('It seems that you have chosen a wrong file or a wrong conversion type!\n\n%s' % (e))

                row['currency_id'] = key
                row['date'] = date
                row['amount'] = amount
                row['amount_currency'] = amount_currency
                row['Net'] = float(row['Net'].replace(',', '.'))
                row['Fee'] = fee
                if key not in fees:
                    key = 'EUR'
                fees[key].append(fee)
                dates[key].append(date)
                all_dates.append(date)
                stripe[key].append(row)

            # Min/Max date from all dates
            min_date = min(all_dates)
            max_date = max(all_dates)

            for key in stripe.keys():
                if not dates[key]:
                    continue
                if sum(fees[key]) != 0:
                    fee_vals = dict(id='txn_fees_stripe_%s_%s%s' % (key.lower(), min_date.replace('-', ''), max_date.replace('-', '')), date=max_date, name='Stripe Gebühren %s - %s (%s)' % (min_date.replace('-', ' '), max_date[-2:], key), amount=-sum(fees[key]), currency_id=key, ref='Automatische Berechnung (Transaktionen)', note='')
                    stripe[key].append(fee_vals)
            
            for currency, lines in stripe.items():
                if len(lines) == 0:
                    continue
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames, dialect=dialect)
                writer.writeheader()
                for line in lines:
                    writer.writerow(line)
                filename = '%s - %s (%s) - Stripe Import (Odoo).csv' % (min_date.replace('-', ' '), max_date[-2:], currency)
                output_vals[filename] = output
                _logger.info('File %s with %s lines to be created', currency, len(lines))
        return output_vals

