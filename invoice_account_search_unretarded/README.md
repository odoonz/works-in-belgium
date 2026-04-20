# Invoice Account Search Unretarded

Restores a sane `account.account.name_search` implementation on invoice and bill lines.

## Why this exists

Odoo's `account.account.name_search` used to do two reasonable things when the
`move_type` context key was set (i.e. when picking an account on an invoice or vendor
bill line):

1. If the user typed anything containing a digit, the hardcoded `account_type` filter
   was **skipped entirely**, so you could find an account by its code (e.g. typing `53`
   on a vendor bill found the accounts in the 53xxx range).
2. The hardcoded type list was **combined** with the caller-supplied domain via
   `Domain.AND`, so downstream modules and view-level `search_default_*` filters could
   legitimately add account types to the dropdown.

Upstream then "fixed" this in
[odoo/odoo#257850](https://github.com/odoo/odoo/pull/257850) — a PR whose stated
rationale is, verbatim, that being able to find an account by its code on an invoice
line is "not intended". The change removes both escape hatches at once. Specifically,
the new `account.account.name_search`:

- Removes the digit-aware branch entirely. Searching by code no longer bypasses the type
  filter, so typing `53` on a vendor bill returns nothing — even though those accounts
  exist, are valid for the bill, and are visible in the search panel.
- Makes the `move_type` → `account_type` mapping absolute and effectively uncustomisable
  from outside `account`. The mapping is hardcoded as:

  ```python
  move_type_accounts = {
      "out": ["income"],
      "in":  ["expense", "asset_fixed"],
  }
  ```

  Anything not in that list (Cost of Revenue / `expense_direct_cost`, liabilities,
  current assets, off-balance, etc.) is silently filtered out of the autocomplete
  dropdown regardless of what the view, the `search_default_*` context keys, or any
  inheriting module tries to do. The only escape hatch that still works is the "Search
  more…" dialog, which goes through the search view and not through `name_search`.

The net effect is that:

- You cannot search accounts by code from an invoice line anymore.
- You cannot extend the allowed account types from a downstream module without
  monkey-patching `name_search`.

The PR was approved and merged in two days flat with no apparent consideration of the
legitimate cases it breaks: anyone with an `expense_direct_cost` account who codes
vendor bills against it, anyone who knows their chart of accounts by code rather than by
name, and any downstream module that previously relied on the `Domain.AND` combine to
add account types to the dropdown. See the discussion on
[odoo/odoo#257850](https://github.com/odoo/odoo/pull/257850) for the full context.

This module restores the previous behaviour by **monkey-patching**
`AccountAccount.name_search` directly on the upstream class, rather than inheriting
`account.account` via `_inherit` and overriding the method. The patch is applied once at
module import time, so any other module that inherits `account.account` and calls
`super().name_search(...)` ends up calling the patched implementation as its parent and
continues to work normally. With this module installed, typing `53` on a vendor bill
again finds accounts by code, and view-level `search_default_type_*` context keys once
again influence the dropdown results — not just the "Search more…" dialog.

The patched function body is copied verbatim from the previous Odoo 19.0 implementation;
no copyright is claimed on it.

## Usage

Install the module. There is no configuration. Any change in upstream
`account.account.name_search` after this module was written will be overridden — review
the implementation if you upgrade Odoo and the upstream method changes again.
