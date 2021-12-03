# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from collections import OrderedDict

from odoo import models
from odoo.tools.safe_eval import safe_eval, time


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
            if (
                len(invoice.line_ids.mapped(invoice.line_ids._get_section_grouping()))
                == 1
            ):
                continue
            sequence = 10
            move_lines = invoice._get_ordered_invoice_lines()
            # Group move lines according to their sale order
            section_grouping_matrix = OrderedDict()
            for move_line in move_lines:
                group = move_line.mapped(move_line._get_section_grouping())
                group_move_line_ids = section_grouping_matrix.get(group)
                if not group_move_line_ids:
                    section_grouping_matrix[group] = [move_line.id]
                else:
                    group_move_line_ids.append(move_line.id)
            # Prepare section lines for each group
            section_lines = []
            for group, move_line_ids in section_grouping_matrix.items():
                section_lines.append(
                    (
                        0,
                        0,
                        {
                            "name": group._get_invoice_section_name(),
                            "display_type": "line_section",
                            "sequence": sequence,
                        },
                    )
                )
                sequence += 10
                for move_line in self.env["account.move.line"].browse(move_line_ids):
                    move_line.sequence = sequence
                    sequence += 10
            invoice.line_ids = section_lines
        return invoice_ids

    def _get_invoice_section_name(self):
        """Returns the text for the section name."""
        self.ensure_one()
        naming_scheme = (
            self.partner_invoice_id.invoice_section_name_scheme
            or self.company_id.invoice_section_name_scheme
        )
        if naming_scheme:
            return safe_eval(naming_scheme, {"object": self, "time": time})
        elif self.client_order_ref:
            return "{} - {}".format(self.name, self.client_order_ref or "")
        else:
            return self.name
