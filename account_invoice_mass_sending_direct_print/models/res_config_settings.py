from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    invoice_is_direct_print = fields.Boolean(
        string="Invoice Is Direct Print",
        related="company_id.invoice_is_direct_print",
        readonly=False,
        help="Allow invoice to be printed directly when 'Send and Print' is clicked",
    )
