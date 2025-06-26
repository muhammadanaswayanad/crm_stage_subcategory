from odoo import api, fields, models


class CrmStageSubcategory(models.Model):
    _name = 'crm.stage.subcategory'
    _description = 'CRM Stage Subcategory'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    _sql_constraints = [
        ('name_stage_uniq', 'unique (name, stage_id)', 'The name must be unique per stage!')
    ]
