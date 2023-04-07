# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class AccountMoveApplyTaxChange(models.TransientModel):
    _name = "account.move.apply.tax.change"
    _description = "Apply a tax change on invoices."

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveApplyTaxChange, self).default_get(fields_list)
        active_model = self.env.context.get("active_model")
        if active_model == "account.invoice":
            invoice_ids = self.env.context.get("active_ids")
            invoices = self.env[active_model].search(
                [
                    ("id", "in", invoice_ids),
                    ("state", "in", ("draft", "open")),
                ]
            )
            res["invoice_ids"] = [(6, 0, invoices.ids)]
        return res

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )
    tax_change_id = fields.Many2one(
        comodel_name="account.tax.change",
        ondelete="cascade",
        required=True,
        string="Tax Change",
        domain="[('company_id', '=', company_id)]",
    )
    invoice_ids = fields.Many2many(
        comodel_name="account.invoice",
        required=True,
        string="Invoices",
        domain=(
            "[('state', 'in', ('draft', 'open')),"
            " ('company_id', '=', company_id),"
            "]"
        ),
    )

    @api.multi
    def validate(self):
        """Apply the tax changes on the selected invoices."""
        self.ensure_one()
        src_taxes = self.tax_change_id.change_line_ids.tax_src_id
        for invoice in self.invoice_ids:
            if self._skip_invoice(invoice):
                continue
            invoice_lines = invoice.invoice_line_ids
            for line in invoice_lines:
                # Skip the line if:
                # - no tax to replace
                if not line.invoice_line_tax_ids & src_taxes:
                    continue
                # - invoice date doesn't match
                if self._skip_line(line):
                    continue
                self._change_taxes(line)
        return True

    def _skip_invoice(self, invoice):
        """No tax change on invoice already posted or paid."""
        return invoice.state == "posted"

    def _skip_line(self, line):
        """No tax change on line if the invoice date doesn't match.

        Other modules could override this method.
        """
        return (
            not line.invoice_id.date_invoice
            or line.invoice_id.date_invoice < self.tax_change_id.date
        )

    def _change_taxes(self, line):
        """Apply the tax change in the invoice line.

        Other modules could override this method.
        """
        line.invoice_line_tax_ids -= self.tax_change_id.change_line_ids.tax_src_id
        line.invoice_line_tax_ids |= self.tax_change_id.change_line_ids.tax_dest_id
        line.invalidate_cache()
        line.modified(["invoice_line_tax_ids"])
        line.recompute()
        line.invoice_id.compute_taxes()
