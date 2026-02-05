# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import Command, _, models

_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def get_mail_values(self, res_ids):
        """Override to apply email layout for mass invoice sending.

        In standard mass_mail mode, emails are created directly without layout template.
        This override wraps body_html with the email layout.
        """
        results = super().get_mail_values(res_ids)

        if (
            not self.env.context.get("account_invoice_mass_sending")
            or self.composition_mode != "mass_mail"
            or self.model != "account.move"
        ):
            return results

        for res_id in res_ids:
            mail_values = results.get(res_id)
            if not mail_values:
                continue

            invoice = self.env["account.move"].browse(res_id)

            # Wrap body_html with email layout template (with button for main recipient)
            body_html = mail_values.get("body_html", "")
            if body_html:
                rendered_body = self._render_body_with_layout_mass_sending(
                    invoice, body_html, has_button_access=True
                )
                if rendered_body:
                    mail_values["body_html"] = rendered_body

        return results

    def _action_send_mail(self, auto_commit=False):
        """Override to send separate emails to followers without button."""
        result = super()._action_send_mail(auto_commit=auto_commit)

        if not self.env.context.get("account_invoice_mass_sending"):
            return result

        if self.composition_mode != "mass_mail" or self.model != "account.move":
            return result

        # Send separate emails to followers
        self._notify_followers_mass_sending(auto_commit=auto_commit)

        return result

    def _notify_followers_mass_sending(self, auto_commit=False):
        """Send separate emails to invoice followers without View button."""
        res_ids = self._context.get("active_ids", [self.res_id])

        for res_id in res_ids:
            invoice = self.env["account.move"].browse(res_id)

            # Get followers (excluding main recipient and author/sender)
            exclude_partner_ids = {invoice.partner_id.id, self.author_id.id}
            follower_partners = invoice.message_follower_ids.mapped("partner_id")
            follower_partners = follower_partners.filtered(
                lambda p: p.email and p.id not in exclude_partner_ids
            )

            if not follower_partners:
                continue

            # Render body without button for followers
            body_html = self._render_field("body", [res_id]).get(res_id, "")
            rendered_body = self._render_body_with_layout_mass_sending(
                invoice, body_html, has_button_access=False
            )

            if not rendered_body:
                continue

            # Create mail.mail for followers
            mail_values = {
                "subject": self._render_field("subject", [res_id]).get(res_id, ""),
                "body_html": rendered_body,
                "email_from": self.email_from,
                "author_id": self.author_id.id,
                "recipient_ids": [Command.link(p.id) for p in follower_partners],
                "model": self.model,
                "res_id": res_id,
                "auto_delete": True,
            }

            mail = self.env["mail.mail"].sudo().create(mail_values)
            mail.send(auto_commit=auto_commit)

    def _render_body_with_layout_mass_sending(
        self, invoice, body_html, has_button_access=True
    ):
        """Render body with email layout template using Odoo native methods."""
        template_xmlid = self.email_layout_xmlid or "mail.mail_notification_layout"

        # Create a minimal mail.message record to get render context from Odoo native
        # We don't save it, just use it to call _notify_by_email_prepare_rendering_context
        message_values = {
            "body": body_html,
            "record_name": invoice.name,
            "model": invoice._name,
            "res_id": invoice.id,
            "message_type": "email",
            # Signature option from wizard
            "email_add_signature": not bool(self.template_id)
            and self.email_add_signature,
        }
        message = self.env["mail.message"].new(message_values)

        model_description = self.env["ir.model"]._get(invoice._name).display_name

        # Get render context from Odoo native method (includes subtitles, signature, etc.)
        render_context = invoice._notify_by_email_prepare_rendering_context(
            message,
            msg_vals=message_values,
            model_description=model_description,
        )

        # Override button access based on parameter
        if has_button_access:
            render_context["has_button_access"] = True
            render_context["button_access"] = {
                "url": invoice._notify_get_action_link("view"),
                "title": _("View %s" % model_description),
            }
        else:
            render_context["has_button_access"] = False
            render_context["button_access"] = {}

        try:
            rendered_body = self.env["ir.qweb"]._render(
                template_xmlid,
                render_context,
                minimal_qcontext=True,
                raise_if_not_found=False,
            )
            if rendered_body:
                rendered_body = self.env["mail.render.mixin"]._replace_local_links(
                    rendered_body
                )
                return rendered_body
        except Exception as e:
            _logger.warning(
                "Failed to render email layout for invoice %s: %s", invoice.name, e
            )

        return None
