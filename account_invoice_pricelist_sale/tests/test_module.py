# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestModule(BaseCommon):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Bob"})
        self.product = self.env["product.product"].create({"name": "rubber band"})
        self.product.invoice_policy = "order"

    def _create_sale_order(self, pricelist=False):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": pricelist and pricelist.id or False,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 5,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                            "qty_delivered": 5,
                        },
                    )
                ],
            }
        )

    def test_invoice_with_pricelist(self):
        """Test invoice creation with pricelist"""
        pricelist = self.env["product.pricelist"].create({"name": "Demo Pricelist"})
        order = self._create_sale_order(pricelist=pricelist)
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertEqual(
            invoice.pricelist_id.id,
            order.pricelist_id.id,
            "Invoice Pricelist has not been recovered from sale order",
        )

    def test_invoice_without_pricelist(self):
        """Test invoice creation without pricelist"""
        order = self._create_sale_order()
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertFalse(
            invoice.pricelist_id,
            "Invoice should not have pricelist when order has none",
        )
