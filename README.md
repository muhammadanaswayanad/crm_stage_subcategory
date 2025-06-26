# CRM Stage Subcategory

This Odoo 17 module adds subcategories to CRM stages to allow for more granular tracking of lead/opportunity stages.

## Features

- **Stage Subcategories**: Manage subcategories for your CRM stages
- **Wizard-based Selection**: A convenient wizard for selecting substages when changing stages
- **Kanban Integration**: Works with drag-and-drop in kanban views
- **Dynamic Filtering**: Only show subcategories related to the selected stage
- **Default Subcategories**: Define a default subcategory for each stage
- **Auto-Selection**: Automatically suggests the default subcategory when changing stages
- **User Interface Integration**: Subcategories visible in list, kanban and form views
- **Archiving**: Ability to archive subcategories that are no longer needed

## Configuration

1. Go to CRM > Configuration > Pipeline > Stage Subcategories to create and manage subcategories
2. Assign subcategories to specific CRM stages
3. Optionally set a default subcategory for each stage
4. When moving opportunities to stages with multiple subcategories, a wizard will automatically appear to select the appropriate subcategory
5. You can also click the "Select Substage" button next to the substage field in the form view

## Technical Information

- Adds a new model `crm.stage.subcategory`
- Adds a wizard model `crm.lead.substage.wizard`
- Extends `crm.lead` with a `sub_stage_id` field
- Uses JavaScript to intercept kanban drag-and-drop events
- Overrides write method to show wizard on stage changes
- Supports active/inactive status and default selection
- Provides helpful error messages with available options

## Security

- Regular users can view subcategories
- Only Sales managers can create/edit/delete subcategories
