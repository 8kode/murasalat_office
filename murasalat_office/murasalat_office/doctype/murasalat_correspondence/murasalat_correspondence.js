// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt

const PARTY_RULES = {
    Internal: {
        source: "Internal",
        target: "Internal"
    },
    Incoming: {
        source: "External",
        target: "Internal"
    },
    Outgoing: {
        source: "Internal",
        target: "External"
    }
};

frappe.ui.form.on("Murasalat Correspondence", {
    setup(frm) {
        frm.set_query("source_entity", () => {
            const rule = PARTY_RULES[frm.doc.correspondence_type];

            if (!rule) {
                return {};
            }

            const filters = {
                entity_type: rule.source,
                active: 1
            };

            if (frm.doc.target_entity) {
                filters.name = ["!=", frm.doc.target_entity];
            }

            return { filters };
        });

        frm.set_query("target_entity", () => {
            const rule = PARTY_RULES[frm.doc.correspondence_type];

            if (!rule) {
                return {};
            }

            const filters = {
                entity_type: rule.target,
                active: 1
            };

            if (frm.doc.source_entity) {
                filters.name = ["!=", frm.doc.source_entity];
            }

            return { filters };
        });
    },

    correspondence_type(frm) {
        frm.set_value("source_entity", null);
        frm.set_value("target_entity", null);
    }
});