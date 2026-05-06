from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    accrued_purchase_stock_account_id = fields.Many2one(
        "account.account",
        string="Purchase Stock Accrual Account",
        check_company=True,
        help="Default liability counterpart for purchase order accruals.",
    )
    accrued_revenue_advance_account_id = fields.Many2one(
        "account.account",
        string="Revenue in Advance Account",
        check_company=True,
        help="Default counterpart for GIND sale order accruals.",
    )
    delivered_in_advance_account_id = fields.Many2one(
        "account.account",
        string="Delivered in Advance Account",
        check_company=True,
        help="Default counterpart for GDNI sale order accruals.",
    )
