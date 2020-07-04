# -*- coding: utf-8 -*-
import logging

from odoo.models import BaseModel

_logger = logging.getLogger(__name__)

RELATED_FIELDS = ['many2one', 'one2many', 'many2many']
TEXT_FIELDS = ['char', 'text', 'html', 'selection']
NUMBER_FIELDS = ['integer', 'float']
DATE_FIELDS = ['date', 'datetime']

def preload_wrapper(loader):
    
    def _get_module_xml_id(self, line, id_idx):
        try:
            module, xmlid = line[id_idx].split('.', 1)
        except ValueError:
            xmlid = line[id_idx]
            module = self._context.get('module', False)
        
        return module, xmlid
    
    def _split_data(self, fields, data):
        """ Helper to load all data and returns both lists found/not found data """
        new_data = []
        old_data = []
        id_idx = fields.index('id')
        for line in data:
            module, xmlid = _get_module_xml_id(self, line, id_idx)
            already_mapped_id = self.env['ir.model.data']._update_dummy(model=self._name, module=module, xml_id=xmlid)
            if not already_mapped_id:
                new_data.append(line)
            else:
                old_data.append(line)
        return new_data, old_data

    def _check_any_changes(self, fields, line):
        """ Check if there are any changes between this line and the database record """

        id_idx = fields.index('id')
        module, xmlid = _get_module_xml_id(self, line, id_idx)
        item = self.env.ref("%s.%s" % (module, xmlid))

        if not item or not item.exists():
            return True

        fields, line = fields[:], line[:]

        del (line[id_idx])
        del (fields[id_idx])

        db_fields = self._fields
        fields_dict = {}
        for idx, field in enumerate(fields):
            field_name = fields[idx].split('/')[0]

            fields_dict.update({
                idx: [field_name, db_fields.get(field_name).type],
            })

        for idx, value in enumerate(line):
            field_name, db_field_type = fields_dict.get(idx, '')
            item_value = getattr(item, field_name, None)
            if item_value is None:
                raise ValueError('Model %s has no attribute %s!' % (item._name, field_name))

            if db_field_type == 'boolean':
                value = True if value and value.lower() == 'true' else False
            elif db_field_type in NUMBER_FIELDS:
                value = float(value) if value else 0.0
                if db_field_type == 'integer':
                    value = int(value) if value else 0
            elif db_field_type in TEXT_FIELDS + DATE_FIELDS:
                value = False if not value else value
            elif db_field_type in RELATED_FIELDS:
                value = any(
                    not self.env.ref(temp_id, raise_if_not_found=False) or
                    self.env.ref(temp_id) not in item_value
                    for temp_id in value.split(',')
                ) if value else False

            if (
                (db_field_type not in RELATED_FIELDS and item_value != value) or
                (db_field_type in RELATED_FIELDS and value)
            ):
                return True
        return False

    def _check_preload_compare(self):
        """ Check if we are installing/upgrading and if Model-Module combination is marked for preload """
        if self.env.get('base.preload.compare', None) is None:
            _logger.debug('Base Preload Compare is not installed')
            return False

        allowed_module = self.sudo().env['base.preload.compare'].search([
            ('module_id.name', '=', self._context.get('module')),
            ('model_ids.model', '=', self._name),
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

        changed_records_count = len(new_data) - new_data_count

        _logger.info(
            'Found: %d new records, %d changed records, %d unchanged records.' %
            (new_data_count, changed_records_count, len(old_data) - changed_records_count)
        )

        return new_data

    def load(self, fields, data):
        if _check_preload_compare(self):
            data = _default_loader(self, fields, data)

        return loader(self, fields, data)

    return load


BaseModel.load = preload_wrapper(BaseModel.load)
