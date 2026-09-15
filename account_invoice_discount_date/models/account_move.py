# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    discount_date = fields.Date(
        compute="_compute_discount_date",
        inverse="_inverse_discount_date",
        store=True,
        help="Last date at which the discounted amount must be paid in order "
        "for the Early Payment Discount to be granted",
    )
    effective_due_date = fields.Date(
        compute="_compute_effective_due_date",
        store=True,
        help="Discount date if an Early Payment Discount applies, "
        "otherwise the regular due date",
    )
    discount_amount_currency = fields.Monetary(
        compute="_compute_discount_amounts",
        store=True,
        currency_field="currency_id",
        help="Total amount to pay, in invoice currency, if the Early "
        "Payment Discount is applied on all lines that grant one",
    )
    discount_balance = fields.Monetary(
        compute="_compute_discount_amounts",
        store=True,
        currency_field="company_currency_id",
        help="Total amount to pay, in company currency, if the Early "
        "Payment Discount is applied on all lines that grant one",
    )

    @api.depends("discount_date", "invoice_date_due")
    def _compute_effective_due_date(self):
        """Discount date takes priority over the regular due date"""
        for record in self:
            record.effective_due_date = record.discount_date or record.invoice_date_due

    @api.depends(
        "line_ids.discount_amount_currency",
        "line_ids.amount_currency",
        "line_ids.discount_balance",
        "line_ids.balance",
    )
    def _compute_discount_amounts(self):
        """Sum discount-or-plain amounts of payment term lines, only when
        at least one of them grants an Early Payment Discount"""
        for record in self:
            payment_lines = record.line_ids.filtered_domain(
                [("display_type", "=", "payment_term")]
            )
            if any(payment_lines.mapped("discount_amount_currency")):
                record.discount_amount_currency = sum(
                    line.discount_amount_currency or line.amount_currency
                    for line in payment_lines
                )
                record.discount_balance = sum(
                    line.discount_balance or line.balance for line in payment_lines
                )
            else:
                record.discount_amount_currency = False
                record.discount_balance = False

    @api.depends("line_ids.discount_date")
    def _compute_discount_date(self):
        """Set discount_date to the earliest Discount date
        of lines with Date maturity"""
        for record in self:
            d_dates = record.line_ids.filtered_domain(
                [
                    ("display_type", "=", "payment_term"),
                    ("discount_date", "!=", False),
                ]
            ).mapped("discount_date")
            new_discount_date = d_dates and sorted(d_dates)[0] or None
            if new_discount_date != record.discount_date or not new_discount_date:
                record.discount_date = new_discount_date

    def _inverse_discount_date(self):
        """When set Discount date, update all move lines with Date maturity"""
        discount_date_field = self._fields["discount_date"]
        for record in self:
            for line in record.line_ids.filtered_domain(
                [("display_type", "=", "payment_term")]
            ):
                line.discount_date = record.discount_date
                self.env.add_to_compute(discount_date_field, record)
