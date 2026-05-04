// Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {accountTaxHelpers} from "@account/helpers/account_tax";
import {patch} from "@web/core/utils/patch";

patch(accountTaxHelpers, {
    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    _get_fixed_amount_product_quantity(evaluation_context) {
        const quantity = evaluation_context.quantity;
        const uom_factor = evaluation_context.uom.factor || 1.0;
        const product_uom_factor = evaluation_context.product.uom_factor || 1.0;
        return (quantity * uom_factor) / product_uom_factor;
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    _get_fixed_amount_quantity_ratio(tax, evaluation_context) {
        const quantity = evaluation_context.quantity;
        if (!quantity || tax.fixed_amount_multiplier === "quantity") {
            return 1.0;
        } else if (tax.fixed_amount_multiplier === "none") {
            return 1.0 / quantity;
        } else if (tax.fixed_amount_multiplier === "product_quantity") {
            return (
                this._get_fixed_amount_product_quantity(evaluation_context) / quantity
            );
        } else if (tax.fixed_amount_multiplier === "product_weight") {
            const ratio =
                this._get_fixed_amount_product_quantity(evaluation_context) / quantity;
            return ratio * (evaluation_context.product.weight || 0.0);
        }
        return 1.0;
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_tax_amount_fixed_amount(tax, batch, raw_base, evaluation_context) {
        const res = super.eval_tax_amount_fixed_amount(...arguments);
        if (tax.amount_type === "fixed") {
            const ratio = this._get_fixed_amount_quantity_ratio(
                tax,
                evaluation_context
            );
            return res * ratio;
        }
        return res;
    },
});
