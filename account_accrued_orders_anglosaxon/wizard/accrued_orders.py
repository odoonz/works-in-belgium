from odoo import api, fields, models

PURCHASE_TYPES = ("grnb", "gbnr")
SALE_TYPES = ("gdni", "gind")


class AccountAccruedOrdersWizard(models.TransientModel):
    _inherit = "account.accrued.orders.wizard"

    account_id = fields.Many2one(
        default=lambda self: self._get_default_accrual_account(),
    )

    def _get_default_accrual_account(self):
        company = self.env.company
        accrual_type = self.env.context.get("accrual_type")
        active_model = self.env.context.get("active_model", "")
        if accrual_type in PURCHASE_TYPES or active_model in (
            "purchase.order",
            "purchase.order.line",
        ):
            return company.accrued_purchase_stock_account_id
        if accrual_type == "gdni":
            return company.delivered_in_advance_account_id
        return company.accrued_revenue_advance_account_id

    @api.model
    def _get_product_expense_and_stock_var_accounts(self, product):
        """Replace the stock variation account with a company-configured
        account so that accrual entries do not disturb the inventory
        valuation balance maintained by stock moves.

        grnb (Received Not Billed)  → purchase_in_advance_account_id
        gbnr (Billed Not Received)  → purchase_in_advance_account_id
        gdni (Delivered Not Invoiced) → uninvoiced_inventory_account_id
        gind (Invoiced Not Delivered) → undelivered_inventory_account_id
        """
        (
            expense_account,
            stock_var_account,
        ) = super()._get_product_expense_and_stock_var_accounts(product)

        if not expense_account or not stock_var_account:
            return (expense_account, stock_var_account)

        company = self.env.company
        accrual_type = self.env.context.get("accrual_type")
        active_model = self.env.context.get("active_model", "")

        if accrual_type in PURCHASE_TYPES or active_model in (
            "purchase.order",
            "purchase.order.line",
        ):
            override = company.purchase_in_advance_account_id
        elif accrual_type == "gdni":
            override = company.uninvoiced_inventory_account_id
        else:
            override = company.undelivered_inventory_account_id

        if override:
            return (expense_account, override)
        return (expense_account, stock_var_account)
