# CRM Stage Subcategory

This Odoo 17 module adds subcategories to CRM stages to allow for more granular tracking of lead/opportunity stages.

## Features

- **Stage Subcategories**: Manage subcategories for your CRM stages
- **Conditional Required Field**: If a stage has subcategories, selecting a subcategory is required
- **Dynamic Filtering**: Only show subcategories related to the selected stage
- **User Interface Integration**: Subcategories visible in list, kanban and form views

## Configuration

1. Go to CRM > Configuration > Stage Subcategories to create and manage subcategories
2. Assign subcategories to specific CRM stages
3. When moving opportunities to stages with subcategories, you'll be required to select the appropriate subcategory

## Technical Information

- Adds a new model `crm.stage.subcategory`
- Extends `crm.lead` with a `sub_stage_id` field
- Uses validation to ensure correct subcategory selection

## Security

- Regular users can view subcategories
- Only Sales managers can create/edit/delete subcategories
