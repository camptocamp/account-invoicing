# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False):
        """Add sections by sale order in the invoice line.

        Order the invoicing lines by sale order and add lines section with
        the sale order name.
        Only do this for invoices targetting multiple sale order
        """
        invoice_ids = super()._create_invoices(grouped=grouped, final=final)
        for invoice in invoice_ids:
            if len(invoice.line_ids.mapped("sale_line_ids.order_id.id")) == 1:
                continue
            so = None
            sequence = 10
            section_lines = []
            lines = invoice.line_ids.sorted(
                key=lambda r: r.sale_line_ids.order_id.id
            ).filtered(lambda r: not r.exclude_from_invoice_tab)
            for line in lines:
                if line.sale_line_ids.order_id and so != line.sale_line_ids.order_id:
                    so = line.sale_line_ids.order_id
                    section_lines.append(
                        (
                            0,
                            0,
                            {
                                "name": so.name,
                                "display_type": "line_section",
                                "sequence": sequence,
                            },
                        )
                    )
                    sequence += 10
                line.sequence = sequence
                sequence += 10
            invoice.line_ids = section_lines

        return invoice_ids
