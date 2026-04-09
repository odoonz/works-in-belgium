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
        help="Default counterpart for sale order accruals (Revenue in Advance).",
    )
    purchase_in_advance_account_id = fields.Many2one(
        "account.account",
        string="Purchase in Advance Account",
        check_company=True,
        help=(
            "Replaces the stock variation account on purchase accrual "
            "perpetual entries so inventory valuation is not disturbed."
        ),
    )
    undelivered_inventory_account_id = fields.Many2one(
        "account.account",
        string="Undelivered Inventory Account",
        check_company=True,
        help=(
            "Replaces the stock variation account on sale accrual "
            "perpetual entries (COGS in advance) so inventory "
            "valuation is not disturbed."
        ),
    )
