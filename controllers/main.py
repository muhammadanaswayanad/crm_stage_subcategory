from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class CrmStageSubcategoryController(http.Controller):
    
    @http.route('/crm_stage_subcategory/debug_wizard/<int:lead_id>/<int:stage_id>', type='http', auth='user')
    def debug_wizard(self, lead_id, stage_id, **kw):
        """Debug endpoint to manually trigger the substage wizard for a specific lead and stage"""
        _logger.info(f"Debug endpoint called for lead_id={lead_id}, stage_id={stage_id}")
        
        lead = request.env['crm.lead'].browse(lead_id)
        if not lead.exists():
            return """
                <html><body>
                    <h2>Error: Lead not found</h2>
                    <p>Could not find lead with ID {}</p>
                </body></html>
            """.format(lead_id)
        
        stage = request.env['crm.stage'].browse(stage_id)
        if not stage.exists():
            return """
                <html><body>
                    <h2>Error: Stage not found</h2>
                    <p>Could not find stage with ID {}</p>
                </body></html>
            """.format(stage_id)
            
        try:
            # Try to open the wizard
            action = lead.action_open_substage_wizard(stage_id)
            
            # Check if we got a valid action
            if not action:
                return """
                    <html><body>
                        <h2>No action returned</h2>
                        <p>The action_open_substage_wizard method didn't return an action.</p>
                    </body></html>
                """
                
            # Return the action details
            return """
                <html><body>
                    <h2>Wizard Debug Info</h2>
                    <pre>{}</pre>
                    <p>To test the wizard in the UI, <a href="#" onclick="
                        odoo.__DEBUG__.services.action.doAction({});
                        return false;
                    ">click here</a>.</p>
                </body></html>
            """.format(action, action)
            
        except Exception as e:
            _logger.exception("Error in debug wizard")
            return """
                <html><body>
                    <h2>Error</h2>
                    <p>{}</p>
                </body></html>
            """.format(e)
