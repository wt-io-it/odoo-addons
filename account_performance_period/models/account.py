# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Performance Period',
        readonly=True, states={'draft': [('readonly', False)]}
    )

    @api.multi
    @api.onchange('date_range_id')
    def onchange_performance_range(self):
        for invoice in self:
            for line in invoice.invoice_line_ids:
                line.date_range_id = invoice.date_range_id
                line.date_start = invoice.date_range_id.date_start
                line.date_end = invoice.date_range_id.date_end

    @api.multi
    @api.onchange('invoice_line_ids')
    def onchange_invoice_lines(self):
        for invoice in self:
            date_range = invoice.date_range_id
            for line in invoice.invoice_line_ids:
                if date_range and date_range != line.date_range_id:
                    invoice.date_range_id = False

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            for line in invoice.invoice_line_ids:
                line._check_performance_dates()

        return super(AccountInvoice, self).invoice_validate()

    @api.model
    def invoice_line_move_line_get(self):
        lines = super(AccountInvoice, self).invoice_line_move_line_get()
        inv_lines = []
        for line in lines:
            inv_line = self.env['account.invoice.line'].browse(line['invl_id'])
            line.update({
                'date_range_id': inv_line.date_range_id.id,
                'date_start': inv_line.date_start,
                'date_end': inv_line.date_end,
            })
            inv_lines.append(line)

        return inv_lines

    @api.model
    def line_get_convert(self, line, part):
        preserve_dict = {
            'date_range_id': line.get('date_range_id'),
            'date_start': line.get('date_start'),
            'date_end': line.get('date_end'),
        }
        line = super(AccountInvoice, self).line_get_convert(line, part)
        line.update(preserve_dict)
        return line

    @api.model
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        return move_lines


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Performance Period',
    )
    date_start = fields.Date(
        string='Performance Start',
        required=False,
    )
    date_end = fields.Date(
        string='Performance End',
        required=False,
    )

    @api.multi
    @api.onchange('date_start', 'date_end')
    def onchange_date_start(self):
        self.ensure_one()
        if self.date_start > self.date_end:
            self.date_end = self._origin.date_end
            _logger.warning('Start date must be before or equal to the end date!')
            return

        remove_range = False
        if self.date_start != self.date_range_id.date_start:
            remove_range = True
        if self.date_end != self.date_range_id.date_end:
            remove_range = True

        if remove_range:
            self.date_range_id = False

    @api.multi
    @api.onchange('date_range_id')
    def onchange_date_range(self):
        self.ensure_one()
        if not self.date_range_id:
            return {}
        self.date_start = self.date_range_id.date_start
        self.date_end = self.date_range_id.date_end

    def _check_performance_dates(self):
        return True


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Performance Period',
    )
    date_start = fields.Date(
        string='Performance Start',
        required=False,
    )
    date_end = fields.Date(
        string='Performance End',
        required=False,
    )

    @api.multi
    @api.onchange('date_start', 'date_end')
    def onchange_date_start(self):
        self.ensure_one()
        if self.date_start > self.date_end:
            self.date_end = self._origin.date_end
            _logger.warning('Start date must be before or equal to the end date!')
            return

        remove_range = False
        if self.date_start != self.date_range_id.date_start:
            remove_range = True
        if self.date_end != self.date_range_id.date_end:
            remove_range = True

        if remove_range:
            self.date_range_id = False

    @api.multi
    @api.onchange('date_range_id')
    def onchange_date_range(self):
        self.ensure_one()
        if not self.date_range_id:
            return {}
        self.date_start = self.date_range_id.date_start
        self.date_end = self.date_range_id.date_end

    @api.one
    def _prepare_analytic_line(self):
        line_dict = super(AccountMoveLine, self)._prepare_analytic_line()
        if len(line_dict) == 1:
            line_dict = line_dict[0]
        else:
            _logger.error('TODO. Handle more than one analytic line')
            raise
        line_dict.update({
            'date_range_id': self.date_range_id.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        })
        return line_dict


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Performance Period',
    )
    date_start = fields.Date(
        string='Performance Start',
        required=True,
    )
    date_end = fields.Date(
        string='Performance End',
        required=True,
    )

    @api.multi
    @api.onchange('date_start', 'date_end')
    def onchange_date_start(self):
        self.ensure_one()
        if self.date_start > self.date_end:
            self.date_end = self._origin.date_end
            _logger.warning('Start date must be before or equal to the end date!')
            return

        remove_range = False
        if self.date_start != self.date_range_id.date_start:
            remove_range = True
        if self.date_end != self.date_range_id.date_end:
            remove_range = True

        if remove_range:
            self.date_range_id = False

    @api.multi
    @api.onchange('date_range_id')
    def onchange_date_range(self):
        self.ensure_one()
        if not self.date_range_id:
            return {}
        self.date_start = self.date_range_id.date_start
        self.date_end = self.date_range_id.date_end
