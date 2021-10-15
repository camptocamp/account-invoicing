from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    external_name = fields.Char(string="External Name")
