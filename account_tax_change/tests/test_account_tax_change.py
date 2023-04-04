# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import tagged

from .common import AccountTaxChangeCommon


@tagged("post_install", "-at_install")
class TestAccountTaxChange(AccountTaxChangeCommon):
    def test_apply_tax_change(self):
        """Apply a tax change A to B on an invoice using tax A."""
        invoice = self.invoice_tax_a
        old_taxes = invoice.invoice_line_ids.tax_ids
        old_amount_tax = invoice.amount_tax
        self.apply_tax_change(self.tax_change_a2b, invoice)
        new_taxes = invoice.invoice_line_ids.tax_ids
        new_amount_tax = invoice.amount_tax
        self.assertNotEqual(old_taxes, new_taxes)
        self.assertEqual(new_taxes, self.tax_sale_b)
        self.assertNotEqual(old_amount_tax, new_amount_tax)

    def test_apply_tax_change_no_change(self):
        """Apply a tax change A to B on an invoice using already tax B."""
        invoice = self.invoice_tax_b
        old_taxes = invoice.invoice_line_ids.tax_ids
        old_amount_tax = invoice.amount_tax
        self.apply_tax_change(self.tax_change_a2b, invoice)
        new_taxes = invoice.invoice_line_ids.tax_ids
        new_amount_tax = invoice.amount_tax
        self.assertEqual(old_taxes, new_taxes, self.tax_sale_b)
        self.assertEqual(old_amount_tax, new_amount_tax)
