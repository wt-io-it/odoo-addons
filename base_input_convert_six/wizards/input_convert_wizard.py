# -*- coding: utf-8 -*-
import datetime
import sys
import itertools
import base64
import csv
import copy
from decimal import Decimal

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
            ('six_transactions', 'Transactions (SIX)'),
            ('six_payments', 'Payments (SIX)')
        ]
    )

    @api.multi
    def _six_transactions_convert_input_method(self, atts, options=None):
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
                'date', 'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 
                'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'note', 'DO NOT IMPORT', 
                'txn_id', 'ref', 'DO NOT IMPORT', 'DO NOT IMPORT', 'amount',
                'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 
                'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 
                'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'name'
            ]
            six_dict = csv.DictReader(StringIO(csv_data), fieldnames=fieldnames, dialect=dialect)
            six = {
                'EUR': []
            }
            dates = copy.deepcopy(six)
            fieldnames_new = fieldnames[:]
            fieldnames_new.insert(0, 'id')
            fieldnames_new.append('partner_id')
            for row in itertools.islice(six_dict, 1, None):
                try:
                    key = 'EUR'
                    date = datetime.datetime.strptime(row['date'], '%d.%m.%Y').strftime('%Y-%m-%d')
                    amount = float(row['amount'].replace(',', '.'))
                    
                except Exception as e:
                    raise UserError('It seems that you have chosen a wrong file or a wrong conversion type!\n\n%s' % (e))

                row['id'] = 'txn_six_transactions_%s' % row['txn_id']
                row['date'] = date
                row['amount'] = amount
                del row['DO NOT IMPORT']
                dates[key].append(date)
                six[key].append(row)

            fieldnames_new = [x for x in fieldnames_new if x != 'DO NOT IMPORT']
            for currency, lines in six.items():
                if len(lines) == 0:
                    continue
                min_date = min(dates[currency])
                max_date = max(dates[currency])

                output = StringIO()
                dialect.delimiter = ','
                writer = csv.DictWriter(output, fieldnames=fieldnames_new, dialect=dialect)
                writer.writeheader()
                for line in lines:
                    writer.writerow(line)
                filename = '%s - %s (%s) - SIX Transaction Import (Odoo).csv' % (min_date.replace('-', ' '), max_date[-2:], currency)
                output_vals[filename] = output
                _logger.info('File %s with %s lines to be created', currency, len(lines))
        return output_vals

    @api.multi
    def _six_payments_convert_input_method(self, atts, options=None):
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
                'date', 'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'note',
                'DO NOT IMPORT', 'DO NOT IMPORT', 'DO NOT IMPORT', 'amount',
                'ref', 'DO NOT IMPORT', 'MWST', 'Total', 'name', 'partner_id'
            ]
            six_dict = csv.DictReader(StringIO(csv_data), fieldnames=fieldnames, dialect=dialect)
            six = {
                'EUR': []
            }
            dates = copy.deepcopy(six)
            fieldnames_new = fieldnames[:]
            fieldnames_new.insert(0, 'id')
            for row in itertools.islice(six_dict, 1, None):
                try:
                    key = 'EUR'
                    date = datetime.datetime.strptime(row['date'], '%d.%m.%Y').strftime('%Y-%m-%d')
                    if not row['amount']:
                        continue
                    amount = float(row['amount'].replace(',', '.'))
                except Exception as e:
                    raise UserError('It seems that you have chosen a wrong file or a wrong conversion type!\n\n%s' % (e))

                row['id'] = 'txn_six_payments_%s' % row['name']
                row['date'] = date
                row['amount'] = -amount
                del row['DO NOT IMPORT']
                row['partner_id'] = 'Six Payment Services Austria GmbH'
                dates[key].append(date)
                six[key].append(row)

            fieldnames_new = [x for x in fieldnames_new if x != 'DO NOT IMPORT']
            for currency, lines in six.items():
                if len(lines) == 0:
                    continue
                min_date = min(dates[currency])
                max_date = max(dates[currency])

                output = StringIO()
                dialect.delimiter = ','
                writer = csv.DictWriter(output, fieldnames=fieldnames_new, dialect=dialect)
                writer.writeheader()
                for line in lines:
                    writer.writerow(line)
                filename = '%s - %s (%s) - SIX Payments Import (Odoo).csv' % (min_date.replace('-', ' '), max_date[-2:], currency)
                output_vals[filename] = output
                _logger.info('File %s with %s lines to be created', currency, len(lines))
        return output_vals

