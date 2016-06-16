# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class MaterialPlanWizardLine(models.TransientModel):
    _name = 'mrp.plan.wizard.line'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Planned Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom_id = fields.Many2one('product.uom', 'UoM', required=True)
    qty_available = fields.Float(string='Available', digits_compute=dp.get_precision('Product Unit of Measure'), compute='_get_product_info', readonly=True)
    qty_forecasted = fields.Float(string='Forecasted', digits_compute=dp.get_precision('Product Unit of Measure'), compute='_get_product_info', readonly=True)
    stock_uom_id = fields.Many2one('product.uom', string='UoM', compute='_get_product_info')
    qty_needed = fields.Float(string='Minimum need', digits_compute=dp.get_precision('Product Unit of Measure'), compute='_get_product_info', default=0, readonly=True)
    bom_avail = fields.Boolean(string='BoM', compute='_get_product_info', readonly=True)
    wizard_id = fields.Many2one('mrp.plan.wizard', string='Material Planning Wizard')

    @api.multi
    @api.onchange('product_id', 'product_qty', 'product_uom_id')
    def _get_product_info(self):
        uom_obj = self.env['product.uom']
        for line in self:
            line.qty_available = line.product_id.qty_available
            line.qty_forecasted = line.product_id.virtual_available

            line.bom_avail = False
            if line.product_id:
                if line.product_id.bom_count > 0:
                    line.bom_avail = True
                line.stock_uom_id = line.product_id.uom_id

            quantity = line.product_qty
            if line.product_uom_id:
                quantity = uom_obj._compute_qty(
                    line.product_uom_id.id,
                    line.product_qty,
                    line.stock_uom_id.id
                )
            diff = quantity - line.qty_available
            if diff < 0:
                diff = 0
            line.qty_needed = diff

    @api.one
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id


class MaterialNeedWizardLine(models.TransientModel):
    _name = 'mrp.need.wizard.line'

    product_id = fields.Many2one(
        'product.product',
        string='Product', readonly=True
    )
    product_qty = fields.Float(
        string='Needed Quantity',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        readonly=True
    )
    product_uom_id = fields.Many2one(
        'product.uom',
        string='UoM',
        readonly=True
    )
    qty_available = fields.Float(
        string='Available',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        compute='_get_product_info',
        readonly=True
    )
    qty_forecasted = fields.Float(
        string='Forecasted',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        compute='_get_product_info',
        readonly=True
    )
    stock_uom_id = fields.Many2one(
        'product.uom',
        string='UoM',
        compute='_get_product_info'
    )
    qty_needed = fields.Float(
        string='Minimum Need',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        compute='_get_product_info',
        readonly=True
    )
    bom_avail = fields.Boolean(
        string='BoM',
        compute='_get_product_info',
        readonly=True
    )
    wizard_id = fields.Many2one(
        'mrp.plan.wizard',
        string='Material Planning Wizard'
    )

    @api.multi
    def _get_product_info(self):
        uom_obj = self.env['product.uom']
        for line in self:
            line.qty_available = line.product_id.qty_available
            line.qty_forecasted = line.product_id.virtual_available

            line.bom_avail = False
            if line.product_id:
                if line.product_id.bom_count > 0:
                    line.bom_avail = True
                line.stock_uom_id = line.product_id.uom_id

            quantity = line.product_qty
            if line.product_uom_id:
                quantity = uom_obj._compute_qty(
                    line.product_uom_id.id,
                    line.product_qty,
                    line.stock_uom_id.id
                )
            diff = quantity - line.qty_available
            if diff < 0:
                diff = 0
            line.qty_needed = diff


class MaterialProductionPlanWizardLine(models.TransientModel):
    _name = 'mrp.production.plan.wizard.line'

    product_id = fields.Many2one(
        'product.product',
        string='Product', readonly=True
    )
    product_qty = fields.Float(
        string='Quantity',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        readonly=True
    )
    product_uom_id = fields.Many2one(
        'product.uom',
        string='UoM',
        readonly=True
    )
    date_planned = fields.Datetime(
        string='Planned Date',
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        string='BoM',
        domain="['|', ('product_id','=', product_id), '&', ('product_tmpl_id.product_variant_ids','=', product_id), ('product_id','=',False)]"
    )
    wizard_id = fields.Many2one(
        'mrp.plan.wizard',
        string='Material Planning Wizard'
    )


class MaterialPlanWizard(models.TransientModel):
    _name = 'mrp.plan.wizard'

    planning_time = fields.Datetime(
        string='Planned Point',
    )
    orders_created = fields.Boolean(
        string='Production Orders created',
    )

    planned_items = fields.One2many(
        'mrp.plan.wizard.line',
        'wizard_id',
        string='Planned Items',
    )
    needed_items = fields.One2many(
        'mrp.need.wizard.line',
        'wizard_id',
        string='Needed Items',
    )
    mrp_production_items = fields.One2many(
        'mrp.production.plan.wizard.line',
        'wizard_id',
        string='Production Plan Items',
    )

    @api.multi
    def report_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        if not self.orders_created:
            self.replace_needed_items()
        return self.env['report'].get_action(self, 'mrp_plan_wizard.mrp_plan_list')

    @api.multi
    def create_production_orders(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'

        for order in self.mrp_production_items:
            vals = {
                'product_id': order.product_id.id,
                'product_qty': order.product_qty,
                'product_uom': order.product_uom_id.id,
                'bom_id': order.bom_id and order.bom_id.id or False,
            }
            if order.date_planned:
                vals.update({'date_planned': order.date_planned})

            self.env['mrp.production'].create(vals)

        self.orders_created = True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.plan.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }

    # TODO: Improve code (ask for mode, etc.)
    @api.multi
    @api.onchange('planned_items')
    def recompute_planned_items(self):
        if len(self.needed_items) > 0:
            values = self._action_calculate_ingredients()
            self.needed_items = [(6, 0, {})]
            self.mrp_production_items = [(6, 0, {})]
            self.planning_time = values['planning_time']
            self.needed_items = values['needed_items']
            self.mrp_production_items = values['mrp_production_items']

    @api.multi
    def replace_needed_items(self):
        self.write({'needed_items': [(6, 0, {})]})
        self.write({'mrp_production_items': [(6, 0, {})]})
        values = self._action_calculate_ingredients()
        self.write(values)

    @api.multi
    def action_calculate_ingredients(self):
        self.replace_needed_items()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.plan.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }

    @api.multi
    def _action_calculate_ingredients(self):
        prod_obj = self.env['mrp.production']
        uom_obj = self.env['product.uom']
        purchase_list = {}
        production_list = {}

        _logger.debug("\n\nGeplante Produkte")
        for line in self.planned_items:
            quantity = line.product_qty
            if line.product_uom_id != line.stock_uom_id:
                quantity = uom_obj._compute_qty(
                    line.product_uom_id.id, line.product_qty,
                    line.stock_uom_id.id
                )
            purchase_list, production_list = prod_obj.get_mrp_planned_list(
                line.product_id, quantity, line.stock_uom_id.id,
                purchase_list=purchase_list, production_list=production_list
            )
            _logger.debug(u"%s: %s %s (Lager: %s %s)", line.product_id.name, line.product_qty, line.product_uom_id.name, line.product_id.qty_available, line.product_uom_id.name)

        _logger.debug("\n\n\nEinkaufsliste")
        digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        record_list = []
        for product, qty in purchase_list.iteritems():
            diff = float_round(qty, precision_digits=digits) - product.qty_available
            if diff < 0:
                diff = 0
            _logger.debug(u"%s: %s %s (Lager: %s %s | Einkaufsbedarf: %s %s)", product.name, float_round(qty, precision_digits=digits), product.uom_id.name, product.qty_available, product.uom_id.name, diff, product.uom_id.name)
            record_list.append(
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': float_round(qty, precision_digits=digits)
                })
            )
        bom_product_list = []
        for product, qty in production_list.iteritems():
            bom = self.env['mrp.bom'].search([
                '|',
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_id', '=', product.id)
            ], limit=1)
            bom_product_list.append(
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': float_round(qty, precision_digits=digits),
                    'bom_id': bom and bom.id or False,
                })
            )

        time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        return {
            'planning_time': time,
            'needed_items': record_list,
            'mrp_production_items': bom_product_list
        }
