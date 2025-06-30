from odoo import api, fields, models


class CrmStageSubcategory(models.Model):
    _name = 'crm.stage.subcategory'
    _description = 'CRM Stage Subcategory'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    is_default = fields.Boolean(string='Default Subcategory', help="Set as the default subcategory for this stage")
    active = fields.Boolean(default=True, help="If unchecked, it will not be visible in the selection")

    _sql_constraints = [
        ('name_stage_uniq', 'unique (name, stage_id)', 'The name must be unique per stage!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Ensure only one default subcategory per stage"""
        records = super().create(vals_list)
        for record in records:
            if record.is_default:
                self._ensure_single_default(record)
        return records
    
    def write(self, vals):
        """Ensure only one default subcategory per stage"""
        res = super().write(vals)
        if 'is_default' in vals and vals['is_default']:
            for record in self:
                self._ensure_single_default(record)
        return res
    
    def _ensure_single_default(self, record):
        """Ensure there's only one default subcategory per stage"""
        if record.is_default:
            other_defaults = self.search([
                ('stage_id', '=', record.stage_id.id),
                ('is_default', '=', True),
                ('id', '!=', record.id)
            ])
            if other_defaults:
                other_defaults.write({'is_default': False})

    def name_get(self):
        """Override name_get to show stage name in brackets for clarity"""
        result = []
        for record in self:
            name = record.name
            if self._context.get('show_stage_name') and record.stage_id:
                name = f"{name} ({record.stage_id.name})"
            result.append((record.id, name))
        return result
