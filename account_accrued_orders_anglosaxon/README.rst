==========================
Anglo-Saxon Accrued Orders
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

In Anglo-Saxon perpetual inventory valuation, the standard Odoo accrued
orders wizard posts all perpetual adjustments to the single
``account_stock_variation_id`` configured on the stock valuation account.
This is architecturally problematic because the same account is used for:

* Inventory valuation closing adjustments
* Purchase accruals (Goods Received Not Billed / Billed Not Received)
* Sale accruals — GIND (Goods Invoiced Not Delivered)
* Sale accruals — GDNI (Goods Delivered Not Invoiced)

These are distinct accounting concepts that should be ring-fenced in
separate accounts for auditability and reconciliation.

This module adds six configurable company-level accounts and overrides
the accrued orders wizard to route entries to the correct account based
on the accrual scenario.  It also sets ``accrual_type`` context on the
enterprise sale accrual menu actions so the wizard can distinguish GDNI
from GIND.

Account Mapping
===============

Sale Accruals — GDNI (Goods Delivered Not Invoiced)
---------------------------------------------------

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Delivered in Advance      | X     |        |
+---------------------------+-------+--------+
| Revenue                   |       | X      |
+---------------------------+-------+--------+
| COGS / Expense            | X     |        |
+---------------------------+-------+--------+
| Uninvoiced Inventory      |       | X      |
+---------------------------+-------+--------+

Sale Accruals — GIND (Goods Invoiced Not Delivered)
---------------------------------------------------

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Revenue                   | X     |        |
+---------------------------+-------+--------+
| Revenue in Advance        |       | X      |
+---------------------------+-------+--------+
| Undelivered Inventory     | X     |        |
+---------------------------+-------+--------+
| COGS / Expense            |       | X      |
+---------------------------+-------+--------+

Purchase Accruals
-----------------

**Received Not Billed**:

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Purchase in Advance       | X     |        |
+---------------------------+-------+--------+
| Purchase Stock Accrual    |       | X      |
+---------------------------+-------+--------+

**Billed Not Received** (reverse):

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Purchase Stock Accrual    | X     |        |
+---------------------------+-------+--------+
| Purchase in Advance       |       | X      |
+---------------------------+-------+--------+

Configuration
=============

1. Go to **Inventory → Configuration → Settings**.
2. Scroll to the **Accrued Orders** section.
3. Set the six accounts:

   **GIND — Invoiced Not Delivered**

   * **Revenue in Advance Account** — counterpart for GIND accruals.
   * **Undelivered Inventory Account** — replaces stock variation for
     GIND COGS adjustments.

   **GDNI — Delivered Not Invoiced**

   * **Delivered in Advance Account** — counterpart for GDNI accruals.
   * **Uninvoiced Inventory Account** — replaces stock variation for
     GDNI COGS adjustments (current asset, carries a CR balance).

   **Purchases**

   * **Purchase Stock Accrual Account** — liability counterpart for
     purchase accruals (e.g. 21250).
   * **Purchase in Advance Account** — replaces stock variation for
     purchase perpetual entries (e.g. 11255).

When configured, the wizard automatically defaults the counterpart
account and routes perpetual adjustment lines to the correct account.
If the accounts are not configured, the wizard falls back to standard
Odoo behaviour.

Credits
=======

* Graeme Gellatly
