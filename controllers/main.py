from odoo import http, models, fields, api, _
from odoo.http import request
import logging
import json
import html

_logger = logging.getLogger(__name__)

class CrmStageSubcategoryController(http.Controller):
    
    @http.route('/crm_stage_subcategory/debug', type='http', auth='user')
    def debug_index(self, **kw):
        """Debug landing page with useful tools"""
        leads = request.env['crm.lead'].search([], limit=10, order='id desc')
        stages = request.env['crm.stage'].search([], order='sequence')
        substages = request.env['crm.stage.subcategory'].search([], limit=20)
        
        html_content = """
            <html>
            <head>
                <title>CRM Substage Debug</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1, h2 { color: #875A7B; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    .btn { 
                        display: inline-block; 
                        padding: 6px 12px; 
                        background-color: #875A7B; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 3px;
                    }
                    .btn:hover { background-color: #68465e; }
                    .card { 
                        border: 1px solid #ddd; 
                        border-radius: 4px; 
                        padding: 16px; 
                        margin-bottom: 20px; 
                    }
                    .pre { 
                        font-family: monospace; 
                        white-space: pre-wrap; 
                        background-color: #f5f5f5;
                        padding: 10px;
                        border-radius: 4px;
                    }
                </style>
            </head>
            <body>
                <h1>CRM Substage Debugging Tools</h1>
                
                <div class="card">
                    <h2>Test Wizard for Specific Lead</h2>
                    <form action="/crm_stage_subcategory/debug_wizard" method="get">
                        <label for="lead_id">Lead ID:</label>
                        <select name="lead_id" required>
        """
        
        # Add lead options
        for lead in leads:
            html_content += f'<option value="{lead.id}">{lead.id} - {html.escape(lead.name)}</option>'
            
        html_content += """
                        </select>
                        <label for="stage_id">Stage:</label>
                        <select name="stage_id" required>
        """
        
        # Add stage options
        for stage in stages:
            html_content += f'<option value="{stage.id}">{html.escape(stage.name)}</option>'
            
        html_content += """
                        </select>
                        <button type="submit" class="btn">Test Wizard</button>
                    </form>
                </div>
                
                <h2>Recent Leads</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Stage</th>
                        <th>Substage</th>
                        <th>Actions</th>
                    </tr>
        """
        
        # Add lead rows
        for lead in leads:
            html_content += f"""
                <tr>
                    <td>{lead.id}</td>
                    <td>{html.escape(lead.name)}</td>
                    <td>{html.escape(lead.stage_id.name) if lead.stage_id else 'None'}</td>
                    <td>{html.escape(lead.sub_stage_id.name) if lead.sub_stage_id else 'None'}</td>
                    <td>
                        <a href="/crm_stage_subcategory/debug_wizard?lead_id={lead.id}&stage_id={lead.stage_id.id}" class="btn">Test Wizard</a>
                    </td>
                </tr>
            """
            
        html_content += """
                </table>
                
                <h2>Available Substages</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Stage</th>
                        <th>Is Default</th>
                    </tr>
        """
        
        # Add substage rows
        for substage in substages:
            html_content += f"""
                <tr>
                    <td>{substage.id}</td>
                    <td>{html.escape(substage.name)}</td>
                    <td>{html.escape(substage.stage_id.name)}</td>
                    <td>{'Yes' if substage.is_default else 'No'}</td>
                </tr>
            """
            
        html_content += """
                </table>
            </body>
            </html>
        """
        
        return html_content
    
    @http.route('/crm_stage_subcategory/debug_wizard', type='http', auth='user')
    def debug_wizard(self, lead_id=None, stage_id=None, **kw):
        """Debug endpoint to manually trigger the substage wizard for a specific lead and stage"""
        if not lead_id or not stage_id:
            return """
                <html><body>
                    <h2>Error: Missing parameters</h2>
                    <p>Both lead_id and stage_id are required.</p>
                    <p><a href="/crm_stage_subcategory/debug">Back to debug page</a></p>
                </body></html>
            """
            
        try:
            lead_id = int(lead_id)
            stage_id = int(stage_id)
        except ValueError:
            return """
                <html><body>
                    <h2>Error: Invalid parameters</h2>
                    <p>Both lead_id and stage_id must be integers.</p>
                    <p><a href="/crm_stage_subcategory/debug">Back to debug page</a></p>
                </body></html>
            """
            
        _logger.info("Debug endpoint called for lead_id=%s, stage_id=%s", lead_id, stage_id)
        
        lead = request.env['crm.lead'].browse(lead_id)
        if not lead.exists():
            return """
                <html><body>
                    <h2>Error: Lead not found</h2>
                    <p>Could not find lead with ID {}</p>
                    <p><a href="/crm_stage_subcategory/debug">Back to debug page</a></p>
                </body></html>
            """.format(lead_id)
        
        stage = request.env['crm.stage'].browse(stage_id)
        if not stage.exists():
            return """
                <html><body>
                    <h2>Error: Stage not found</h2>
                    <p>Could not find stage with ID {}</p>
                    <p><a href="/crm_stage_subcategory/debug">Back to debug page</a></p>
                </body></html>
            """.format(stage_id)
            
        try:
            # Try to open the wizard
            action = lead.with_context(force_substage_wizard=True).action_open_substage_wizard(stage_id)
            
            # Check if we got a valid action
            if not action:
                return """
                    <html><body>
                        <h2>No action returned</h2>
                        <p>The action_open_substage_wizard method didn't return an action.</p>
                        <p><a href="/crm_stage_subcategory/debug">Back to debug page</a></p>
                    </body></html>
                """
                
            # Format the action for display
            formatted_action = json.dumps(action, indent=2)
            
            # Return the action details with styling
            return """
                <html>
                <head>
                    <title>Wizard Debug Info</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1, h2 { color: #875A7B; }
                        pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow: auto; }
                        .btn { 
                            display: inline-block; 
                            padding: 8px 16px; 
                            background-color: #875A7B; 
                            color: white; 
                            text-decoration: none; 
                            border-radius: 3px;
                            margin-right: 10px;
                        }
                        .btn:hover { background-color: #68465e; }
                    </style>
                    <script src="/web/static/lib/jquery/jquery.js"></script>
                    <script>
                        function executeAction() {
                            if (window.odoo && window.odoo.__DEBUG__) {
                                odoo.__DEBUG__.services.action.doAction({});
                                return true;
                            } else {
                                alert("Odoo Debug mode not detected. Please make sure you are in debug mode.");
                                return false;
                            }
                        }
                    </script>
                </head>
                <body>
                    <h1>Wizard Debug Information</h1>
                    <p><a href="/crm_stage_subcategory/debug" class="btn">Back to Debug Page</a></p>
                    <p>
                        <a href="#" onclick="executeAction(); return false;" class="btn">Open Wizard</a>
                        <small>(This button will only work if you're in debug mode)</small>
                    </p>
                    
                    <h2>Action Details:</h2>
                    <pre>{}</pre>
                </body>
                </html>
            """.format(formatted_action)
            
        except Exception as e:
            _logger.exception("Error in debug wizard")
            return """
                <html><body>
                    <h2>Error</h2>
                    <p>{}</p>
                    <p><a href="/crm_stage_subcategory/debug">Back to debug page</a></p>
                </body></html>
            """.format(e)
