# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    fixed_amount_multiplier = fields.Selection(
        [
            ("none", "No Multiplier"),
            ("quantity", "Quantity (default)"),
            ("product_quantity", "Product Quantity"),
            ("product_weight", "Product Weight"),
        ],
        string="Multiplier",
        required=True,
        default="quantity",
        help="Controls how the quantity is used for fixed-amount taxes:\n"
        "- No Multiplier: the amount is applied once per line.\n"
        "- Quantity (default): multiplied by the line quantity, regardless "
        "of the unit of measure.\n"
        "- Product Quantity: the line quantity is converted to the product's "
        "unit of measure before multiplying.\n"
        "- Product Weight: multiplied by the total weight "
        "(product quantity × product weight).",
    )

    def _get_fixed_amount_product_quantity(self, evaluation_context):
        """Return the quantity expressed in the product's unit of measure."""
        self.ensure_one()
        quantity = evaluation_context["quantity"]
        uom_factor = evaluation_context["uom"].get("factor", 1.0) or 1.0
        product_uom_factor = evaluation_context["product"].get("uom_factor", 1.0) or 1.0
        return quantity * uom_factor / product_uom_factor

    def _get_fixed_amount_quantity_ratio(self, evaluation_context):
        """Return the ratio between the effective quantity and the line quantity.

        This ratio is applied to the standard fixed tax result (which already
        uses the line quantity) to adjust for the selected multiplier mode.
        """
        self.ensure_one()
        quantity = evaluation_context["quantity"]
        if not quantity or self.fixed_amount_multiplier == "quantity":
            return 1.0
        elif self.fixed_amount_multiplier == "none":
            return 1.0 / quantity
        elif self.fixed_amount_multiplier == "product_quantity":
            return (
                self._get_fixed_amount_product_quantity(evaluation_context) / quantity
            )
        elif self.fixed_amount_multiplier == "product_weight":
            ratio = (
                self._get_fixed_amount_product_quantity(evaluation_context) / quantity
            )
            return ratio * evaluation_context["product"].get("weight", 0.0)
        return 1.0

    def _eval_tax_amount_fixed_amount(self, batch, raw_base, evaluation_context):
        res = super()._eval_tax_amount_fixed_amount(batch, raw_base, evaluation_context)
        if self.amount_type == "fixed":
            ratio = self._get_fixed_amount_quantity_ratio(evaluation_context)
            return res * ratio
        return res

    def _eval_taxes_computation_prepare_product_fields(self):
        fields = super()._eval_taxes_computation_prepare_product_fields()
        fields.add("uom_factor")
        fields.add("weight")
        return fields

    def _eval_taxes_computation_prepare_product_uom_fields(self):
        fields = super()._eval_taxes_computation_prepare_product_uom_fields()
        fields.add("factor")
        return fields
