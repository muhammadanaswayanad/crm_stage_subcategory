/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

// Patch the KanbanRecord to intercept the stage change
patch(KanbanRecord.prototype, "crm_stage_subcategory", {
    setup() {
        this._super(...arguments);
        this.state = useState({});
    },

    /**
     * Override the record_do_action method to intercept stage changes
     * and potentially open the substage wizard if needed
     */
    async record_do_action(data, ctx) {
        if (
            data.type === "object" && 
            data.name === "write" && 
            this.props.record.resModel === "crm.lead" && 
            data.context && 
            data.context.stage_id !== undefined
        ) {
            // Extract the new stage_id from the context
            const newStageId = data.context.stage_id;
            const leadId = this.props.record.resId;
            
            // Check if the target stage has subcategories
            const hasSubcategories = await this._checkStageHasSubcategories(newStageId);
            
            if (hasSubcategories) {
                // Open the substage selection wizard
                return this.openSubstageWizard(leadId, newStageId);
            }
        }
        
        // Default behavior if not a stage change or no subcategories
        return this._super(data, ctx);
    },

    /**
     * Check if the given stage has active subcategories
     */
    async _checkStageHasSubcategories(stageId) {
        const subcategories = await this.env.services.orm.searchCount("crm.stage.subcategory", [
            ["stage_id", "=", stageId],
            ["active", "=", true],
        ]);
        return subcategories > 1; // Only intercept if multiple substages exist
    },

    /**
     * Open the substage selection wizard
     */
    async openSubstageWizard(leadId, stageId) {
        return this.env.services.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead.substage.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_lead_id: leadId,
                default_stage_id: stageId,
            },
        });
    },
});
