from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sub_stage_id = fields.Many2one(
        'crm.stage.subcategory', 
        string='Substage',
        domain="[('stage_id', '=', stage_id), ('active', '=', True)]",
        tracking=True,
        help="Additional classification within the stage"
    )
    
    def action_open_substage_wizard(self, stage_id=False):
        """Open a wizard to select the substage when changing stage"""
        self.ensure_one()
        target_stage_id = stage_id or self.stage_id.id
        
        _logger.info("[SUBSTAGE] Button clicked! action_open_substage_wizard called for lead: %s, stage_id=%s",
                    self.id, target_stage_id)
        
        # Check if the target stage has subcategories
        subcategories = self.env['crm.stage.subcategory'].search([
            ('stage_id', '=', target_stage_id),
            ('active', '=', True)
        ])
        
        # Add detailed logging
        _logger.info("[SUBSTAGE] Found %s subcategories: %s",
                    len(subcategories), subcategories.mapped('name'))
        
        # Always show the wizard, even if there are no substages
        action = {
            'name': _('Select Substage'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.substage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'flags': {'headless': False},  # Ensure dialog is shown with header
            'context': {
                'default_lead_id': self.id,
                'default_stage_id': target_stage_id,
            }
        }
        
        # Try to get the view ID but don't fail if not found
        try:
            view = self.env.ref('crm_stage_subcategory.crm_lead_substage_wizard_view_form')
            if view:
                action['view_id'] = view.id
                _logger.info("[SUBSTAGE] Using view_id: %s", view.id)
        except Exception as e:
            _logger.warning("[SUBSTAGE] Could not find view: %s", str(e))
        
        _logger.info("[SUBSTAGE] Returning wizard action: %s", action)
        return action

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
                
    def write(self, vals):
        """Override write to intercept stage changes and open substage wizard if needed"""
        # Store the original stage_id values before write
        if 'stage_id' in vals and self and not self.env.context.get('skip_substage_wizard'):
            # Only process if there's a stage change and substage wizard should not be skipped
            new_stage_id = vals['stage_id']
            
            # Check if the target stage has substages
            substages_count = self.env['crm.stage.subcategory'].search_count([
                ('stage_id', '=', new_stage_id),
                ('active', '=', True)
            ])
            
            _logger.info("Write method intercepted stage change to %s, found %s substages",
                         new_stage_id, substages_count)
            
            # If there are any substages and this isn't coming from our wizard,
            # we should intercept the stage change and open the wizard
            if substages_count >= 1 and not self.env.context.get('from_substage_wizard'):
                # We need to handle one record at a time for the wizard
                if len(self) == 1:
                    _logger.info("Opening substage wizard for lead %s and stage %s",
                                self.id, new_stage_id)
                    # Store the value to be set in the wizard
                    action = self.action_open_substage_wizard(new_stage_id)
                    if action:
                        _logger.info("Got wizard action, proceeding with partial write and returning action")
                        # Don't update the stage yet - will be done by the wizard
                        vals.pop('stage_id')
                        # First perform the write without stage_id
                        super().write(vals)
                        # Return the wizard action
                        return action
        
        # Default behavior - perform the write normally
        _logger.info("Proceeding with normal write: %s", vals)
        return super().write(vals)
