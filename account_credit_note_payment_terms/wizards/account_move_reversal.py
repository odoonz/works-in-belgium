# Copyright 2015 Graeme Gellatly, O4SB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountMoveReversal(models.TransientModel):

    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        vals = super()._prepare_default_reversal(move)
        if move.is_invoice(include_receipts=True):
            vals['invoice_payment_term_id'] = move.invoice_payment_term_id.id
        return vals
