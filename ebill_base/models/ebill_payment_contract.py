# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EbillPaymentContract(models.Model):

    _name = "ebill.payment.contract"
    _description = "Ebill Payment Contract"
    _rec_name = "name"

    transmit_method_id = fields.Many2one(
        comodel_name="transmit.method",
        string="Transmit method",
        ondelete="restrict",
    )
    partner_id = fields.Many2one(comodel_name="res.partner", required=True)
    name = fields.Char(related="partner_id.name")
    date_start = fields.Date(string="Start date")
    date_end = fields.Date(string="End date")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("open", "Open"), ("cancel", "Cancel")],
        required=True,
        default='draft',
    )
    is_valid = fields.Boolean(compute="_compute_is_valid")

    @api.multi
    @api.depends("state")
    def _compute_is_valid(self):
        """ Check that the contract is valid

        It has a start and end date and has not expired.
        """
        for contract in self:
            contract.is_valid = (
                contract.state == "open"
                and contract.date_start
                # Could be optional ?
                and contract.date_end
                and (contract.date_start <= fields.Date.today() <=
                     contract.date_end)
            )
