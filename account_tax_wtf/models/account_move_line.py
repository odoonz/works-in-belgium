# Copyright (C) 2024 Graeme Gellatly
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def write(self, vals):
        if list(vals.keys()) == ["partner_id"]:
            self = self.with_context(skip_invoice_sync=True)
        return super().write(vals)
