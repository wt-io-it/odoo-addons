# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    dedicated_direction_journal = fields.Boolean(
        string="Dedicated direction",
        help="Check if you want to have a dedicated journal for invoice direction role change"
    )
    invoice_direction_role = fields.Boolean(
        string="Reverse direction",
        help="Applicable only for invoice direction stated"
    )

    @api.multi
    def action_create_new(self):
        action = super(AccountJournal, self).action_create_new()
        action['context'].update({'default_invoice_direction_role': self.invoice_direction_role})
        return action

    @api.multi
    def open_action(self):
        action = super(AccountJournal, self).open_action()
        action['context'].update({'default_invoice_direction_role': self.invoice_direction_role})
        return action


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_direction_role = fields.Boolean(
        string="Reverse direction",
        readonly=True, states={'draft': [('readonly', False)]}
    )

    @api.multi
    def invoice_validate(self):
        last_day = self.env.user.company_id.fiscalyear_last_day
        last_month = self.env.user.company_id.fiscalyear_last_month
        for invoice in self:
            date_invoice = invoice.date_invoice
            if not date_invoice:
                date_invoice = fields.Date.today()

            if date_invoice > fields.Date.today():
                raise UserError('You try to validate an invoice for a date in the future!')

            business_type = 'sale'
            if invoice.type in ['in_invoice', 'in_refund']:
                business_type = 'purchase'

            year = date_invoice.year
            fiscal_year_end = date(year, last_month, last_day)
            this_fiscal_year_date = fiscal_year_end
            if this_fiscal_year_date >= date_invoice:
                fiscal_year_end = date((year - 1), last_month, last_day)
            else:
                this_fiscal_year_date = date((year + 1), last_month, last_day)
            last_fiscal_year_date = fiscal_year_end

            # Check whether a journal is allowed or not before validating
            journal = invoice.journal_id
            if journal.dedicated_direction_journal and invoice.invoice_direction_role != journal.invoice_direction_role:
                raise UserError('You try to validate an invoice for a journal which is not properly aligned for this type of invoice!')

            if business_type == 'purchase' and invoice.invoice_direction_role or business_type == 'sale' and not invoice.invoice_direction_role:
                domain = [
                    ('date_invoice', '!=', False),
                    ('id', '!=', invoice.id),
                    ('type', '=', invoice.type),
                    ('invoice_direction_role', '=', invoice.invoice_direction_role)
                ]
                # Check for draft invoices which will be made impossible
                domain_draft = domain[:]
                domain_draft.append(('date_invoice', '<=', this_fiscal_year_date))
                domain_draft.append(('date_invoice', '<', date_invoice))
                domain_draft.append(('date_invoice', '>', last_fiscal_year_date))

                domain_draft.append(('state', 'in', ['draft']))

                if invoice.search(domain_draft, limit=500, order='date_invoice DESC'):
                    raise UserError('There is a draft invoice prior the current invoice date for this configured invoice type!\n')

                # Check for journal and already validated invoices
                domain.append(('date_invoice', '<=', this_fiscal_year_date))
                domain.append(('date_invoice', '>', date_invoice))
                domain.append(('date_invoice', '>', last_fiscal_year_date))
                domain.append(('state', 'not in', ['cancel', 'draft']))
                domain.append(('journal_id', '=', invoice.journal_id.id))
                if invoice.search(domain):
                    raise UserError('There is another validated invoice after the current invoice date for this configured invoice type and journal!')

        return super(AccountInvoice, self).invoice_validate()

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        _logger.info('Journal was changed')
        pass

    @api.onchange('invoice_direction_role')
    def onchange_invoice_direction_role_auto_data(self):
        invoice = self
        business_type = 'sale'
        if invoice.type in ['in_invoice', 'in_refund']:
            business_type = 'purchase'
        if business_type == 'purchase' and invoice.invoice_direction_role or business_type == 'sale' and not invoice.invoice_direction_role:
            invoice.date_invoice = False
        invoice.journal_id = False

        journal_type = business_type
        domain = [
            ('type', '=', journal_type)
        ]
        journal_ids = invoice.env['account.journal'].search(domain)
        direction_role = invoice.invoice_direction_role
        journal_ids = journal_ids.filtered(lambda r: r.dedicated_direction_journal and r.invoice_direction_role == direction_role or not r.dedicated_direction_journal)
        if len(journal_ids) == 1:
            invoice.journal_id = journal_ids.id

        domain = [('id', 'in', journal_ids.ids)]
        domain_dict = {'journal_id': domain}

        return {'domain': domain_dict}
