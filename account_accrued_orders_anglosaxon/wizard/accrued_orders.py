from odoo import fields, models


class AccountAccruedOrdersWizard(models.TransientModel):
    _inherit = "account.accrued.orders.wizard"

    account_id = fields.Many2one(
        default=lambda self: self._get_default_accrual_account(),
    )

    def _get_default_accrual_account(self):
        accrual_type = self.env.context.get("accrual_type")
        if accrual_type:
            handler = getattr(
                self, f"_get_{accrual_type}_default_account", None
            )
            if handler:
                return handler()
        return self.env["account.account"]

    def _get_gdni_default_account(self):
        return self.env.company.delivered_in_advance_account_id

    def _get_gind_default_account(self):
        return self.env.company.accrued_revenue_advance_account_id

    def _get_grnb_default_account(self):
        return self.env.company.accrued_purchase_stock_account_id

    def _get_gbnr_default_account(self):
        return self.env.company.accrued_purchase_stock_account_id
