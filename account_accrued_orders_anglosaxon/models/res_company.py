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
    undelivered_inventory_account_id = fields.Many2one(
        "account.account",
        string="Undelivered Inventory Account",
        check_company=True,
        help=(
            "Replaces the stock variation account on GIND sale accrual "
            "perpetual entries (COGS invoiced in advance of delivery) "
            "so inventory valuation is not disturbed."
        ),
    )
    delivered_in_advance_account_id = fields.Many2one(
        "account.account",
        string="Delivered in Advance Account",
        check_company=True,
        help=(
            "Default counterpart for GDNI sale accruals "
            "(Goods Delivered Not Invoiced)."
        ),
    )
    uninvoiced_inventory_account_id = fields.Many2one(
        "account.account",
        string="Uninvoiced Inventory Account",
        check_company=True,
        help=(
            "Replaces the stock variation account on GDNI sale accrual "
            "perpetual entries (COGS for goods delivered but not yet "
            "invoiced) so inventory valuation is not disturbed."
        ),
    )
