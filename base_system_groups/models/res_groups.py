# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.base.res.res_users import name_selection_groups, name_boolean_group, is_boolean_group, get_boolean_group, is_selection_groups
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class GroupsView(models.Model):
    _inherit = "res.groups"

    system_group = fields.Boolean(string='System Managed Group')

    @api.model
    def _update_user_groups_view(self):
        return super(GroupsView, self.sudo())._update_user_groups_view()

    @api.model
    def create(self, vals):
        if 'system_group' in vals and not self.env.user._is_superuser():
            del vals['system_group']
        return super(GroupsView, self).create(vals)

    @api.multi
    def write(self, vals):
        for group in self:
            if ('system_group' in vals or group.system_group) and not group.env.user._is_superuser():
                raise ValidationError('It is not allowed to write on the system group %s' % group.name)
        return super(GroupsView, self).write(vals)

    @api.multi
    def unlink(self):
        for group in self:
            if group.system_group and not group.env.user._is_superuser():
                raise ValidationError('It is not allowed to delete the system group %s' % group.name)
        return super(GroupsView, self).unlink()


class UsersView(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        self._check_system_group(vals)
        return super(UsersView, self).create(vals)

    @api.multi
    def write(self, vals):
        self._check_system_group(vals)
        return super(UsersView, self).write(vals)

    def _check_system_group(self, vals):
        for key, val in vals.items():
            if is_boolean_group(key):
                val = get_boolean_group(key)
            if val and (is_boolean_group(key) or is_selection_groups(key)):
                groups = self.env['res.groups'].browse(val)
                groups |= groups.mapped('trans_implied_ids')
                if groups and groups.filtered(lambda r: r.system_group) and not self.env.user._is_superuser():
                    raise ValidationError('You are not allowed to assign the system group %s' % ', '.join(g.name for g in groups.filtered(lambda r: r.system_group)))

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(UsersView, self).fields_get(allfields, attributes=attributes)
        if self.env.user._is_superuser():
            return res
        # add reified groups fields
        for app, kind, gs in self.env['res.groups'].sudo().get_groups_by_application():
            gs_system = gs.filtered(lambda r: r.system_group)
            if gs_system:
                gs_filtered = gs.filtered(lambda r: not r.system_group)
                if kind == 'selection':
                    if gs_filtered:
                        # selection group field
                        tips = ['%s: This group can only be assigned by the system user! %s' % (g.name, g.comment if g.comment else '') if g.system_group else '%s: %s' % (g.name, g.comment) for g in gs if g.comment or g.system_group]
                        res[name_selection_groups(gs.ids)] = {
                            'type': 'selection',
                            'string': app.name or _('Other'),
                            'selection': [(False, '')] + [(g.id, '[SYSTEM] %s' % g.name if g.system_group else g.name) for g in gs],
                            'help': '\n'.join(tips),
                            'exportable': False,
                            'selectable': False,
                        }
                    else:
                        del res[name_selection_groups(gs.ids)]
                else:
                    for g in gs_system:
                        del res[name_boolean_group(g.id)]
        return res
