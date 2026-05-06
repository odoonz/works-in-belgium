from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    accrued_purchase_stock_account_id = fields.Many2one(
        related="company_id.accrued_purchase_stock_account_id",
        readonly=False,
    )
    accrued_revenue_advance_account_id = fields.Many2one(
        related="company_id.accrued_revenue_advance_account_id",
        readonly=False,
    )
    delivered_in_advance_account_id = fields.Many2one(
        related="company_id.delivered_in_advance_account_id",
        readonly=False,
    )
