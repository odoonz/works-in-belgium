from odoo import api, fields, models


class AccountAccruedOrdersWizard(models.TransientModel):
    _inherit = "account.accrued.orders.wizard"

    account_id = fields.Many2one(
        default=lambda self: self._get_default_accrual_account(),
    )

    def _get_default_accrual_account(self):
        active_model = self.env.context.get("active_model", "")
        company = self.env.company
        if active_model in ("purchase.order", "purchase.order.line"):
            return company.accrued_purchase_stock_account_id
        return company.accrued_revenue_advance_account_id

    @api.model
    def _get_product_expense_and_stock_var_accounts(self, product):
        """Replace the stock variation account with a company-configured
        account so that accrual entries do not disturb the inventory
        valuation balance maintained by stock moves.

        Purchase side → purchase_in_advance_account_id
        Sale side     → undelivered_inventory_account_id
        """
        (
            expense_account,
            stock_var_account,
        ) = super()._get_product_expense_and_stock_var_accounts(product)

        if not expense_account or not stock_var_account:
            return (expense_account, stock_var_account)

        company = self.env.company
        active_model = self.env.context.get("active_model", "")

        if active_model in ("purchase.order", "purchase.order.line"):
            override = company.purchase_in_advance_account_id
        else:
            override = company.undelivered_inventory_account_id

        if override:
            return (expense_account, override)
        return (expense_account, stock_var_account)
