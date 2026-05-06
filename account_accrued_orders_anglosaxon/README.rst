==========================
Anglo-Saxon Accrued Orders
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

Background
==========

In Anglo-Saxon perpetual inventory valuation the standard Odoo accrued
orders wizard posts all entries — both the balance-sheet counterpart and
the perpetual COGS/expense adjustment — using a single
``account_stock_variation_id`` for the perpetual leg.

When monthly stock closing is enabled, Odoo's stock closing cron pushes
all timing mismatches and valuation errors to the stock variation
account.  This account therefore represents the cumulative sum of
unresolved differences between goods movements and their financial
counterparts (invoices / receipts).

Accrual entries exist to **resolve** those same timing mismatches — they
recognise revenue or expense that the stock closing has already parked in
stock variation.  For this reason the perpetual leg of the accrual entry
**must** use the stock variation account: it is unwinding the balance
that the stock closing placed there.

What This Module Does
=====================

This module adds three configurable company-level **counterpart**
accounts and overrides the accrued orders wizard to:

1. **Default the wizard counterpart account** based on the accrual
   scenario (GDNI / GIND / GRNB / GBNR).
2. **Leave the perpetual (COGS) leg on stock variation** — it is not
   replaced.

The ``accrual_type`` context is set on each of the four enterprise menu
actions so the wizard can distinguish the scenario and pick the correct
default.

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
| **Stock Variation**       |       | X      |
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
| **Stock Variation**       | X     |        |
+---------------------------+-------+--------+
| COGS / Expense            |       | X      |
+---------------------------+-------+--------+

Purchase Accruals — Received Not Billed
---------------------------------------

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| **Stock Variation**       | X     |        |
+---------------------------+-------+--------+
| Purchase Stock Accrual    |       | X      |
+---------------------------+-------+--------+

Purchase Accruals — Billed Not Received (reverse)
--------------------------------------------------

+---------------------------+-------+--------+
| Account                   | Debit | Credit |
+===========================+=======+========+
| Purchase Stock Accrual    | X     |        |
+---------------------------+-------+--------+
| **Stock Variation**       |       | X      |
+---------------------------+-------+--------+

Configuration
=============

1. Go to **Inventory → Configuration → Settings**.
2. Scroll to the **Accrued Orders** section.
3. Set three accounts:

   * **Revenue in Advance Account** — counterpart for GIND accruals.
   * **Delivered in Advance Account** — counterpart for GDNI accruals.
   * **Purchase Stock Accrual Account** — liability counterpart for
     purchase accruals.

When configured, the wizard automatically defaults the counterpart
account based on the accrual scenario.  Perpetual entries always use the
product category's stock variation account — this is intentional so that
the accrual unwinds the balance that monthly stock closing placed there.

If the accounts are not configured, the wizard falls back to standard
Odoo behaviour.

Credits
=======

* Graeme Gellatly
