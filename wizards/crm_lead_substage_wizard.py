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
            
            # Set default substage if available
            if substages and not wizard.sub_stage_id:
                default_substage = substages.filtered(lambda s: s.is_default)
                if default_substage:
                    wizard.sub_stage_id = default_substage[0].id
                else:
                    wizard.sub_stage_id = substages[0].id

    def action_apply(self):
        """Apply the selected substage to the lead/opportunity"""
        self.ensure_one()
        if self.lead_id and self.stage_id:
            vals = {'stage_id': self.stage_id.id}
            if self.sub_stage_id:
                vals['sub_stage_id'] = self.sub_stage_id.id
            
            # Use context to avoid recursion when writing stage_id
            self.lead_id.with_context(
                from_substage_wizard=True, 
                skip_substage_wizard=True
            ).write(vals)
        
        return {'type': 'ir.actions.act_window_close'}
