from odoo import api, fields, models


class AccountAccruedOrdersWizard(models.TransientModel):
    _inherit = "account.accrued.orders.wizard"

    account_id = fields.Many2one(
        default=lambda self: self._get_default_accrual_account(),
    )

    def _get_default_accrual_account(self):
        accrual_type = self.env.context.get("accrual_type")
        if accrual_type:
            return getattr(self, f"_get_{accrual_type}_default_account")()
        return self.env["account.account"]

    def _get_gdni_default_account(self):
        return self.env.company.delivered_in_advance_account_id

    def _get_gind_default_account(self):
        return self.env.company.accrued_revenue_advance_account_id

    def _get_grnb_default_account(self):
        return self.env.company.accrued_purchase_stock_account_id

    def _get_gbnr_default_account(self):
        return self.env.company.accrued_purchase_stock_account_id

    @api.model
    def _get_product_expense_and_stock_var_accounts(self, product):
        """Replace the stock variation account with a company-configured
        account so that accrual entries do not disturb the inventory
        valuation balance maintained by stock moves.

        Each accrual_type dispatches to its own method so the mapping
        is explicit and individually overridable.
        """
        (
            expense_account,
            stock_var_account,
        ) = super()._get_product_expense_and_stock_var_accounts(product)

        if not expense_account or not stock_var_account:
            return (expense_account, stock_var_account)

        if accrual_type := self.env.context.get("accrual_type"):
            handler = getattr(
                self, f"_get_{accrual_type}_stock_var_account", None
            )
            if handler:
                stock_var_account = handler() or stock_var_account
        return (expense_account, stock_var_account)

    def _get_gdni_stock_var_account(self):
        return self.env.company.uninvoiced_inventory_account_id

    def _get_gind_stock_var_account(self):
        return self.env.company.undelivered_inventory_account_id
