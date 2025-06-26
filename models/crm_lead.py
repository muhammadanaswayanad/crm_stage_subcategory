from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sub_stage_id = fields.Many2one(
        'crm.stage.subcategory', 
        string='Substage',
        domain="[('stage_id', '=', stage_id), ('active', '=', True)]",
        tracking=True,
        help="Additional classification within the stage"
    )

    @api.constrains('stage_id', 'sub_stage_id')
    def _check_substage_required(self):
        for lead in self:
            if lead.stage_id and lead.sub_stage_id:
                # Ensure the selected substage belongs to the selected stage
                if lead.sub_stage_id.stage_id != lead.stage_id:
                    raise ValidationError(
                        f"The selected substage '{lead.sub_stage_id.name}' does not belong to "
                        f"the current stage '{lead.stage_id.name}'. Please select a valid substage."
                    )
                
            elif lead.stage_id:
                # Check if the stage has any subcategories that are required
                subcategories = self.env['crm.stage.subcategory'].search([
                    ('stage_id', '=', lead.stage_id.id),
                    ('active', '=', True)
                ])
                
                # Only show warning for stages with multiple subcategories
                if len(subcategories) > 1 and not lead.sub_stage_id:
                    # Get the first 5 subcategory names for display
                    subcategory_names = ", ".join([sub.name for sub in subcategories[:5]])
                    if len(subcategories) > 5:
                        subcategory_names += "..."
                    
                    # Use a warning message instead of validation error to make it less intrusive
                    # This allows users to proceed even without selecting a substage
                    lead._message_log(body=_(
                        f"<p class='text-warning'><strong>Note:</strong> "
                        f"Consider selecting a substage for '{lead.stage_id.name}'. "
                        f"Available options: {subcategory_names}</p>"
                    ))

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Reset substage when stage changes and suggest a default if available"""
        if not self.stage_id:
            self.sub_stage_id = False
            return
            
        # If subcategory doesn't belong to the selected stage, reset it
        if self.sub_stage_id and self.sub_stage_id.stage_id != self.stage_id:
            self.sub_stage_id = False
            
        # Get subcategories for this stage
        subcategories = self.env['crm.stage.subcategory'].search([
            ('stage_id', '=', self.stage_id.id),
            ('active', '=', True)
        ])
        
        # If there's only one subcategory, select it automatically
        if len(subcategories) == 1:
            self.sub_stage_id = subcategories.id
            return
            
        # Try to suggest a default subcategory
        if not self.sub_stage_id and subcategories:
            # First try to find the default marked subcategory
            default_subcategory = subcategories.filtered(lambda s: s.is_default)
            
            # If no default is found, use the first one by sequence
            if not default_subcategory:
                default_subcategory = subcategories[0]
            
            if default_subcategory:
                self.sub_stage_id = default_subcategory.id
