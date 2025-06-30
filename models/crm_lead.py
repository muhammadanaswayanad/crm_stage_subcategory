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
        
        # Special case: if there's exactly one substage, set it directly and don't show wizard
        if len(subcategories) == 1 and not self.env.context.get('force_substage_wizard'):
            _logger.info("[SUBSTAGE] Only one substage found (%s), setting it directly without wizard",
                        subcategories.name)
            self.with_context(
                from_substage_wizard=True, 
                skip_substage_wizard=True,
                skip_substage_check=True  # Skip the constraint check
            ).write({'sub_stage_id': subcategories.id})
            
            # Show a notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Substage Set'),
                    'message': _("Substage '%s' has been automatically selected") % subcategories.name,
                    'sticky': False,
                    'type': 'success',
                }
            }
        
        # If there are multiple substages or if forced, show the wizard
        action = {
            'name': _('Select Substage'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.substage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'flags': {
                'headless': False,  # Ensure dialog is shown with header
                'clear_breadcrumbs': True,  # Don't add to breadcrumbs
            },
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
        except Exception as e:
            _logger.warning("[SUBSTAGE] Could not find view: %s", str(e))
        
        _logger.info("[SUBSTAGE] Returning wizard action: %s", action)
        return action

    @api.constrains('stage_id', 'sub_stage_id')
    def _check_substage_required(self):
        for lead in self:
            # Only validate if we have both a stage and a substage
            if lead.stage_id and lead.sub_stage_id:
                # Check if the stage and substage don't match 
                if lead.sub_stage_id.stage_id != lead.stage_id:
                    # Instead of validation error, auto-clear the substage and log a message
                    old_substage_name = lead.sub_stage_id.name
                    _logger.info(
                        "Automatically clearing substage '%s' as it doesn't belong to stage '%s'",
                        old_substage_name, lead.stage_id.name
                    )
                    
                    # Use sudo to avoid recursion with the constraint
                    lead.with_context(skip_substage_check=True).write({
                        'sub_stage_id': False
                    })
                    
                    # Log message to chatter with HTML formatting
                    lead.message_post(
                        body=f"<p>{_('Substage')} '<strong>{old_substage_name}</strong>' {_('was automatically cleared as it doesn\'t belong to the current stage.')}</p>",
                        subject=_("Substage Cleared"),
                        message_type='notification',
                        subtype_id=self.env.ref('mail.mt_note').id
                    )
            
            # Add a suggestion for adding substage if available but not selected
            elif lead.stage_id:
                # Skip if we're in the middle of another write operation
                if self.env.context.get('skip_substage_check'):
                    continue
                    
                # Check if the stage has any subcategories that could be selected
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
                    
                    # Use a warning message to suggest selecting a substage
                    lead._message_log(body=_(
                        "<p class='text-warning'><strong>Note:</strong> "
                        "Consider selecting a substage for '<strong>%s</strong>'. "
                        "Available options: <em>%s</em></p>") % (lead.stage_id.name, subcategory_names)
                    )

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Reset substage when stage changes and suggest a default if available"""
        # Always clear the substage when stage changes
        previous_substage = self.sub_stage_id.name if self.sub_stage_id else False
        self.sub_stage_id = False
        
        # Exit if no stage is selected
        if not self.stage_id:
            return
            
        _logger.info("Stage changed, looking for substages for stage_id=%s", self.stage_id.id)
            
        # Get subcategories for this stage
        subcategories = self.env['crm.stage.subcategory'].search([
            ('stage_id', '=', self.stage_id.id),
            ('active', '=', True)
        ])
        
        _logger.info("Found %s substages for stage '%s'", 
                    len(subcategories), self.stage_id.name)
        
        # If no substages exist, leave substage empty
        if not subcategories:
            return
            
        # If there's only one subcategory, select it automatically
        if len(subcategories) == 1:
            self.sub_stage_id = subcategories.id
            return
            
        # Try to suggest a default subcategory
        # First try to find the default marked subcategory
        default_subcategory = subcategories.filtered(lambda s: s.is_default)
        
        # If no default is found, use the first one by sequence
        if default_subcategory:
            self.sub_stage_id = default_subcategory[0].id
            _logger.info("Set default substage: %s", default_subcategory[0].name)
        else:
            # Don't automatically set substage if there are multiple options without a default
            _logger.info("Multiple substages available but no default set, leaving empty")
                
    def write(self, vals):
        """Override write to intercept stage changes and open substage wizard if needed"""
        # Store the original stage_id values before write
        if 'stage_id' in vals and self and not self.env.context.get('skip_substage_wizard'):
            # Only process if there's a stage change and substage wizard should not be skipped
            new_stage_id = vals['stage_id']
            old_stage_id = self.stage_id.id if self.stage_id else False
            
            # Skip if there's no actual change in stage
            if new_stage_id == old_stage_id:
                _logger.info("Stage not changing, proceeding with normal write")
                return super().write(vals)
                
            _logger.info("Stage changing from %s to %s", old_stage_id, new_stage_id)
            
            # Check if the target stage has substages
            substages = self.env['crm.stage.subcategory'].search([
                ('stage_id', '=', new_stage_id),
                ('active', '=', True)
            ])
            
            _logger.info("Write method intercepted stage change to %s, found %s substages",
                         new_stage_id, len(substages))
            
            # Always clear the substage when changing stage (regardless of wizard)
            if 'sub_stage_id' not in vals:
                vals['sub_stage_id'] = False
            
            # If there are substages and this isn't coming from our wizard,
            # we should intercept the stage change and open the wizard
            if substages and not self.env.context.get('from_substage_wizard'):
                # Handle special case: if there's exactly one substage, set it directly
                if len(substages) == 1:
                    _logger.info("Only one substage available (%s), setting it automatically", 
                                substages.name)
                    vals['sub_stage_id'] = substages.id
                    return super().write(vals)
                
                # We need to handle one record at a time for the wizard
                if len(self) == 1:
                    _logger.info("Opening substage wizard for lead %s and stage %s",
                                self.id, new_stage_id)
                    
                    # First perform the write WITH the stage_id to actually change the stage
                    # The form view will stay open while the wizard pops up
                    super().write(vals)
                    
                    # Open the wizard but don't block the stage change
                    return self.action_open_substage_wizard(new_stage_id)
        
        # Default behavior - perform the write normally
        _logger.info("Proceeding with normal write: %s", vals)
        return super().write(vals)
