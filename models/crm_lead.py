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
                subcategories = self.env['crm.stage.subcategory'].search([
                    ('stage_id', '=', lead.stage_id.id)
                ])
                
                if subcategories and not lead.sub_stage_id:
                    subcategory_names = ", ".join([sub.name for sub in subcategories[:5]])
                    if len(subcategories) > 5:
                        subcategory_names += "..."
                    
                    raise ValidationError(
                        f"The substage is required for stage '{lead.stage_id.name}'. "
                        f"Please select one of the following: {subcategory_names}"
                    )
                
                # Ensure the selected substage belongs to the selected stage
                if lead.sub_stage_id and lead.sub_stage_id.stage_id != lead.stage_id:
                    lead.sub_stage_id = False

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Reset substage when stage changes and suggest a default if available"""
        if not self.stage_id:
            self.sub_stage_id = False
            return
            
        # If subcategory doesn't belong to the selected stage, reset it
        if self.sub_stage_id and self.sub_stage_id.stage_id != self.stage_id:
            self.sub_stage_id = False
            
        # Try to suggest a default subcategory
        if not self.sub_stage_id:
            # First try to find the default marked subcategory
            default_subcategory = self.env['crm.stage.subcategory'].search([
                ('stage_id', '=', self.stage_id.id),
                ('is_default', '=', True),
                ('active', '=', True)
            ], limit=1)
            
            # If no default is found, use the first one by sequence
            if not default_subcategory:
                default_subcategory = self.env['crm.stage.subcategory'].search([
                    ('stage_id', '=', self.stage_id.id),
                    ('active', '=', True)
                ], order='sequence, id', limit=1)
            
            if default_subcategory:
                self.sub_stage_id = default_subcategory.id
