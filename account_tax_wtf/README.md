# Account Tax WTF

## Problem Description

This module addresses a critical issue in Odoo's accounting system where manually edited taxes get overwritten during invoice
posting.

### The Issue

In the core Odoo `account` module, specifically in `account_move.py` around line 5641, there's code that synchronizes partner
IDs on move lines with the invoice's commercial partner:

```python
# From odoo/addons/account/models/account_move.py lines 5633-5641
for invoice in to_post:
    # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
    # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
    wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(lambda aml:
        aml.partner_id != invoice.commercial_partner_id
        and aml.display_type not in ('line_section', 'line_subsection', 'line_note')
    )
    if wrong_lines:
        wrong_lines.write({'partner_id': invoice.commercial_partner_id.id})
```

This code is intended to fix inconsistencies that might occur during concurrent editing, but it has an unintended side effect:
**changing the `partner_id` on move lines triggers a complete tax recalculation**, which overwrites any manually set or edited
taxes on the invoice lines.

### The Solution

The `account_tax_wtf` module intercepts the `write` method on `account.move.line` and adds a context flag
`skip_invoice_sync=True` when only the `partner_id` is being changed. This prevents the automatic tax recalculation that would
otherwise overwrite manually configured taxes.

```python
# From models/account_move_line.py
def write(self, vals):
    if list(vals.keys()) == ["partner_id"]:
        self = self.with_context(skip_invoice_sync=True)
    return super().write(vals)
```

## Installation

This module depends on the `account` module and will automatically install when added to your Odoo addons path.

## Usage

The module works transparently - once installed, it will prevent tax recalculation when Odoo synchronizes partner IDs during
invoice posting, preserving any manually edited taxes.

## Compatibility

- Odoo 19.0
- Requires the standard `account` module

## Author

Graeme Gellatly https://moahub.nz
