{
    'name': 'CRM Stage Subcategory',
    'version': '17.0.1.3.0',
    'category': 'Sales/CRM',
    'summary': 'Add subcategories to CRM stages',
    'description': """
        This module allows you to create subcategories for CRM stages.
        It adds a new model for subcategories and extends the CRM lead model with a
        subcategory field that integrates seamlessly with the standard Odoo stage widget.
        Subcategories can be archived and marked as default for a stage.
        
        The module respects the standard Odoo UI and enhances it with additional categorization
        capabilities within each stage.
    """,
    'author': 'Custom Development',
    'website': '',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_stage_subcategory_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
