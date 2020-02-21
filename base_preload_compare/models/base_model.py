# -*- coding: utf-8 -*-
import logging

from odoo.models import BaseModel

_logger = logging.getLogger(__name__)


def preload_wrapper(loader):
    def _split_data(self, fields, data):
        """ Helper to load all data and returns both lists found/not found data """
        new_data = []
        old_data = []
        id_idx = fields.index('id')
        for line in data:
            try:
                module, xmlid = line[id_idx].split('.', 1)
            except ValueError:
                xmlid = line[id_idx]
                module = self._context.get('module', False)
            already_mapped_id = self.env['ir.model.data']._update_dummy(model=self._name, module=module, xml_id=xmlid)
            if not already_mapped_id:
                new_data.append(line)
            else:
                old_data.append(line)
        return new_data, old_data

    def _check_any_changes(self, fields, line):
        """ Check if there are any changes between this line and the database record """

        id_idx = fields.index('id')
        try:
            module, xmlid = line[id_idx].split('.', 1)
        except ValueError:
            xmlid = line[id_idx]
            module = self._context.get('module', False)
        item = self.env.ref("%s.%s" % (module, xmlid))

        if not item or not item.exists():
            return True

        fields, line = fields[:], line[:]

        del (line[id_idx])
        del (fields[id_idx])

        db_fields = self._fields
        fields_dict = {}
        for idx, field in enumerate(fields):
            field_data = fields[idx].split('/')
            field_name = field_data[0]
            field_type = None

            if len(field_data) > 1:
                field_type = field_data[1]

            fields_dict.update({
                idx: [field_name, field_type, db_fields.get(field_name).type],
            })

        for idx, value in enumerate(line):
            field_name, field_type, db_field_type = fields_dict.get(idx, '')
            item_value = getattr(item, field_name, None)
            if item_value is None:
                raise ValueError('Model %s has no attribute %s!' % (item._name, field_name))

            if db_field_type == 'float':
                value = float(value) if value else 0.0
            elif db_field_type == 'integer':
                value = int(value) if value else 0
            elif db_field_type == 'boolean':
                value = True if value.lower() == 'true' else False

            if not field_type and item_value != value and bool(item_value) != bool(value):
                return True
            elif (
                    field_type == 'id' and
                    value and
                    any(
                        not self.env.ref(temp_id, raise_if_not_found=False) or
                        self.env.ref(temp_id) not in item_value
                        for temp_id in value.split(',')
                    )
            ):
                return True

        return False

    def _check_preload_compare(self):
        """ Check if we are installing/upgrading and if Model-Module combination is marked for preload """
        allowed_module = self.env['base.preload.compare'].search([
            ('module_id.name', '=', self._context.get('module')),
            ('model_ids.model', '=', self._name)
        ])

        return self._context.get('mode', '') in ['update', 'init'] and allowed_module

    def _default_loader(self, fields, data):
        ''' Check old data for changes and add them to new data if changes were found '''

        _logger.info(
            'Loading %d records of type \'%s\' in module \'%s\'.' %
            (len(data), self._name, self._context.get('module', False))
        )

        new_data, old_data = _split_data(self, fields, data)
        new_data_count = len(new_data)

        if new_data or old_data:
            for line in old_data:
                if _check_any_changes(self, fields, line):
                    new_data.append(line)

        _logger.info(
            'Found: %d new records, %d changed records, %d unchanged records.' %
            (new_data_count, len(new_data) - new_data_count, len(old_data))
        )

        return new_data

    def load(self, fields, data):
        if _check_preload_compare(self):
            data = _default_loader(self, fields, data)

        return loader(self, fields, data)

    return load


BaseModel.load = preload_wrapper(BaseModel.load)
