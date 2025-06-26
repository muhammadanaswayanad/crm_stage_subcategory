from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sub_stage_id = fields.Many2one(
        'crm.stage.subcategory', 
        string='Substage',
        domain="[('stage_id', '=', stage_id)]",
        tracking=True
    )

    @api.constrains('stage_id', 'sub_stage_id')
    def _check_substage_required(self):
        for lead in self:
            if lead.stage_id:
                # Check if the stage has any subcategories
                subcategories_count = self.env['crm.stage.subcategory'].search_count([
                    ('stage_id', '=', lead.stage_id.id)
                ])
                
                if subcategories_count > 0 and not lead.sub_stage_id:
                    raise ValidationError(
                        f"The substage is required for stage '{lead.stage_id.name}' as it has defined subcategories."
                    )
                
                # Ensure the selected substage belongs to the selected stage
                if lead.sub_stage_id and lead.sub_stage_id.stage_id != lead.stage_id:
                    lead.sub_stage_id = False

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Reset substage when stage changes"""
        if self.stage_id and self.sub_stage_id and self.sub_stage_id.stage_id != self.stage_id:
            self.sub_stage_id = False
