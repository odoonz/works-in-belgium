# Purchase Stock SVL Skip Invoice Sync

## Problem

When an invoice is validated and there are price differences, corresponding Stock Value Layers are created, but also the invoice
is synced and so any adjustments of tax (e.g. when the supplier calculated differently and was off by a cent) will be reverted.

In particular, Odoo's `purchase_stock` module, in the `_post` method of the `account.move` model (account_invoice.py currently
line 129) will call

```
        if valued_lines:
            svls, _amls = valued_lines._apply_price_difference()
            stock_valuation_layers |= svls
```

and the `apply_price_difference` method of the `account.move.line` model (account_move_line.py currently line 53) will call

```
return self.env['stock.valuation.layer'].sudo().create(svl_vals_list), self.env['account.move.line'].sudo().create(aml_vals_list)
```

and this creation triggers tax recalculation on the invoice, reverting any manual adjustments.

### Solution

We set the context key `skip_invoice_sync` to avoid tax recalculation:

```
from odoo import models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _apply_price_difference(self):
        """Skip invoice sync so tax adjustments are not reverted"""
        return super().with_context(skip_invoice_sync=True)._apply_price_difference()
```

## Installation

This module depends on the `purchase_stock` module. Once installed, it injects the above-described change to invoice validation.
