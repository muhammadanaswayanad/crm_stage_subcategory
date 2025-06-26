/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";

// Store the original function for later use
const originalRecordDoAction = KanbanRecord.prototype.record_do_action;

// Patch the KanbanRecord to intercept the stage change
patch(KanbanRecord.prototype, {
    /**
     * Check if the given stage has active subcategories
     */
    async _checkStageHasSubcategories(stageId) {
        console.log("Checking substages for stage:", stageId);
        const subcategories = await this.env.services.orm.searchCount("crm.stage.subcategory", [
            ["stage_id", "=", stageId],
            ["active", "=", true],
        ]);
        console.log(`Found ${subcategories} subcategories for stage ${stageId}`);
        return subcategories >= 1; // Show wizard if there's any substage
    },

    /**
     * Open the substage selection wizard
     */
    async openSubstageWizard(leadId, stageId) {
        console.log(`Opening substage wizard for lead ${leadId} and stage ${stageId}`);
        return this.env.services.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead.substage.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_lead_id: leadId,
                default_stage_id: stageId,
                from_kanban_js: true,
            },
        });
    },

    /**
     * Override the record_do_action method to intercept stage changes
     * and potentially open the substage wizard if needed
     */
    async record_do_action(data, ctx) {
        // For debugging purposes
        console.log("record_do_action called with data:", data);
        
        try {
            if (
                this.props.record.resModel === "crm.lead" && 
                data.type === "object" && 
                data.name === "write" && 
                data.context && 
                data.context.stage_id !== undefined
            ) {
                // Extract the new stage_id from the context
                const newStageId = data.context.stage_id;
                const leadId = this.props.record.resId;
                
                console.log(`Intercepted stage change for lead ${leadId} to stage ${newStageId}`);
                
                // Check if the target stage has subcategories
                const hasSubcategories = await this._checkStageHasSubcategories(newStageId);
                
                if (hasSubcategories) {
                    console.log(`Opening substage wizard for lead ${leadId} and stage ${newStageId}`);
                    // Open the substage selection wizard
                    return this.openSubstageWizard(leadId, newStageId);
                }
            }
            
            // Default behavior if not a stage change or no subcategories
            console.log("Proceeding with original action");
            return originalRecordDoAction.call(this, data, ctx);
        } catch (error) {
            console.error("Error in record_do_action override:", error);
            return originalRecordDoAction.call(this, data, ctx);
        }
    },
});
