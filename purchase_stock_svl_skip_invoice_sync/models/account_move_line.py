# Copyright (C) 2025 MoaHub Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _apply_price_difference(self):
        """Skip invoice sync so tax adjustments are not reverted"""
        return super(
            AccountMoveLine, self.with_context(skip_invoice_sync=True)
        )._apply_price_difference()
