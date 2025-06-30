from odoo import api, fields, models, _


class CrmLeadSubstageWizard(models.TransientModel):
    _name = 'crm.lead.substage.wizard'
    _description = 'Select Substage for Lead/Opportunity'

    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', required=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True)
    sub_stage_id = fields.Many2one(
        'crm.stage.subcategory', 
        string='Substage',
        domain="[('stage_id', '=', stage_id), ('active', '=', True)]",
    )
    available_substage_ids = fields.Many2many(
        'crm.stage.subcategory', 
        string='Available Substages',
        compute='_compute_available_substages'
    )
    has_substages = fields.Boolean(string='Has Substages', compute='_compute_available_substages')

    @api.depends('stage_id')
    def _compute_available_substages(self):
        for wizard in self:
            substages = self.env['crm.stage.subcategory'].search([
                ('stage_id', '=', wizard.stage_id.id),
                ('active', '=', True)
            ])
            wizard.available_substage_ids = substages
            wizard.has_substages = bool(substages)
            
            # Log for debugging
            _logger = self.env.cr.logger
            _logger.info(f"[SUBSTAGE_WIZARD] Computing available substages for stage_id={wizard.stage_id.id}, found {len(substages)} substages")
            
            # Set default substage if available
            if substages and not wizard.sub_stage_id:
                default_substage = substages.filtered(lambda s: s.is_default)
                if default_substage:
                    _logger.info(f"[SUBSTAGE_WIZARD] Setting default substage: {default_substage[0].name}")
                    wizard.sub_stage_id = default_substage[0].id
                elif substages:
                    _logger.info(f"[SUBSTAGE_WIZARD] Setting first substage: {substages[0].name}")
                    wizard.sub_stage_id = substages[0].id

    def action_apply(self):
        """Apply the selected substage to the lead/opportunity"""
        self.ensure_one()
        _logger = self.env.cr.logger
        _logger.info(f"[SUBSTAGE_WIZARD] Apply button clicked. Lead: {self.lead_id.id}, Stage: {self.stage_id.id}, Substage: {self.sub_stage_id.id if self.sub_stage_id else 'None'}")
        
        # Make the substage required if there are multiple substages
        if self.has_substages and not self.sub_stage_id:
            _logger.warning(f"[SUBSTAGE_WIZARD] No substage selected but required")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Substage Required'),
                    'message': _('Please select a substage for the current stage.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        if self.lead_id and self.stage_id:
            vals = {'stage_id': self.stage_id.id}
            if self.sub_stage_id:
                vals['sub_stage_id'] = self.sub_stage_id.id
            else:
                vals['sub_stage_id'] = False  # Clear substage if none selected
            
            _logger.info(f"[SUBSTAGE_WIZARD] Writing values to lead: {vals}")
            
            # Use context to avoid recursion when writing stage_id
            self.lead_id.with_context(
                from_substage_wizard=True, 
                skip_substage_wizard=True
            ).write(vals)
            
            # Add a message to the chatter
            stage_name = self.stage_id.name
            substage_name = self.sub_stage_id.name if self.sub_stage_id else "None"
            self.lead_id.message_post(
                body=_(f"Stage updated to '{stage_name}' with substage '{substage_name}'"),
                subject=_("Substage Updated")
            )
        
        _logger.info(f"[SUBSTAGE_WIZARD] Closing wizard")
        return {'type': 'ir.actions.act_window_close'}
