==========================
Anglo-Saxon Accrued Orders
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

In Anglo-Saxon perpetual inventory valuation, the standard Odoo accrued
orders wizard posts all perpetual adjustments to the
``account_stock_variation_id`` derived from the stock valuation account.
This is problematic because the same account ends up mixing:

* Inventory valuation closing adjustments
* Purchase accruals (Goods Received Not Billed / Billed Not Received)
* Sale accruals (Goods Delivered Not Invoiced / Goods Invoiced Not Delivered)

Posting directly to the stock valuation account is also wrong because
it creates a mismatch between the inventory balance maintained by stock
moves and the GL balance.

This module overrides the accrued orders wizard so that perpetual
adjustment lines hit **company-configured accounts** instead of the
stock variation (or stock valuation) account:

* **Purchases** → ``purchase_in_advance_account_id``
* **Sales** → ``undelivered_inventory_account_id`` (COGS in advance)

This keeps accrual entries cleanly separated from both the stock
variation account used by closing entries and the stock valuation
account used by inventory moves.

The wizard also defaults the counterpart account based on the order
type — **Purchases Accrual** for purchase orders and **Revenue in
Advance** for sale orders — both configurable per company.

Account Mapping
===============

Sale Accruals
-------------

**GDNI — Goods Delivered Not Invoiced** (performance obligation complete):

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Revenue in Advance        | X     |        |
+---------------------------+-------+--------+
| Revenue                   |       | X      |
+---------------------------+-------+--------+
| COGS / Expense            | X     |        |
+---------------------------+-------+--------+
| Undelivered Inventory     |       | X      |
+---------------------------+-------+--------+

**GIND — Goods Invoiced Not Delivered** (reverse):

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
| Purchases Accrual         |       | X      |
+---------------------------+-------+--------+

**Billed Not Received** (reverse):

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Purchases Accrual         | X     |        |
+---------------------------+-------+--------+
| Purchase in Advance       |       | X      |
+---------------------------+-------+--------+

Configuration
=============

1. Go to **Inventory → Configuration → Settings**.
2. Scroll to the **Accrued Orders** section.
3. Set the accounts:

   **Sale side:**

   * **Revenue in Advance Account** — counterpart for sale accruals
     (e.g. 21280).
   * **Undelivered Inventory Account** — replaces stock variation for
     sale perpetual entries / COGS in advance (e.g. 11250).

   **Purchase side:**

   * **Purchase Stock Accrual Account** — liability counterpart for
     purchase accruals (e.g. 21250).
   * **Purchase in Advance Account** — replaces stock variation for
     purchase perpetual entries (e.g. 21270).

When configured, the wizard automatically defaults the counterpart
account based on the order type and routes perpetual lines to the
configured accounts.  If the perpetual accounts are not configured
the wizard falls back to the stock variation account from the product
category (base Odoo behaviour).

Credits
=======

* Graeme Gellatly
