# -*- coding: utf-8 -*-
import datetime
import sys
import base64
import csv
from decimal import Decimal
from odoo import http

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2


class InputConvertOutput(models.TransientModel):
    _name = 'input.convert.output'
    _description = 'Output Files'
    
    wizard_id = fields.Many2one(
        comodel_name='input.convert.wizard',
        string='Input Wizard'
    )
    file_name = fields.Char(string='Filename')
    output_file = fields.Binary(
        string='Output File',
        filename='file_name',
        attachment=True
    )


class InputConvertWizard(models.TransientModel):
    _name = 'input.convert.wizard'
    _description = 'Input Files'

    input_file = fields.Binary(
        string='Input File',
        filename='file_name',
        attachment=True
    )
    file_name = fields.Char(string='Filename')
    conversion_type = fields.Selection(
        string='Conversion Type',
        selection=[]
    )
    output_file_ids = fields.One2many(
        comodel_name='input.convert.output',
        inverse_name='wizard_id',
        string='Output Files'
    )

    def _get_attachements(self, fieldname):
        atts = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', self._name),
            ('res_field', '=', fieldname),
            ('res_id', 'in', self.ids),
        ])
        return atts

    @api.multi
    def action_wizard_close(self):
        action = self.env.ref('base.action_open_website').read()[0]
        action['url'] = '/web?#'
        return action

    @api.multi
    def action_wizard_new(self):
        new_wizard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'input.convert.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': new_wizard.id,
            'target': 'new',
            'context': new_wizard._context,
        }

    @api.multi
    def action_convert_input(self):
        self.ensure_one()
        if self.input_file and self.conversion_type:
            atts = self._get_attachements('input_file')
            file_name = self.file_name
            if file_name and '.csv' in file_name.lower():
                mimetype = 'text/csv'
            else:
                vals = {
                    'datas': self.input_file,
                    'datas_fname': file_name
                }
                mimetype = self.env['ir.attachment']._compute_mimetype(vals)
            atts.name = self.file_name
            atts.datas_fname = self.file_name
            atts.mimetype = mimetype

            conv_method_name = '_%s_convert_input_method' % (self.conversion_type)
            if hasattr(self, conv_method_name):
                method = getattr(self, conv_method_name)
                output_vals = method(atts)
                output_files = self.output_file_ids
                for name, stream in output_vals.items():
                    stream_value = stream.getvalue()
                    if not PY2:
                        stream_value = bytes(stream_value.encode('utf-8'))
                    content = base64.b64encode(stream_value)
                    output_file = {
                        'wizard_id': self.id,
                        'output_file': content,
                        'file_name': name,
                    }
                    output_files |= self.output_file_ids.create(output_file)
                self.output_file_ids = output_files
            else:
                raise UserError('There is no method defined to convert your input file!')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'input.convert.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }
