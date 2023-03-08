===================
L10n Nz Tax Periods
===================

Use dates as per tax year for tax closing entry

Configuration
=============

Provided this module is in your addons path, it will autoinstall if l10n_nz is installed. However it
may be manually installed for other localizations.

If your VAT/GST reporting period does not align with the fiscal year, you can set the Parameter `vat_period_end` in
the format `MM-DD`.

Usage
=====

To use this module there is nothing to do by default. It will automatically determine the GST Reporting Period
for closing entry from the fiscalyear settings on the company. If the GST/VAT reporting does not align with the fiscal
year you can set the Parameter `vat_period_end` in the format `MM-DD`.


Known Issues
============

Because a config parameter is used this will apply globally in a multicompany setup. Unfortunately, without making overly
complex, and not wanting to add fields for something that Odoo should obviously just fix, this is the decision.

Current Odoo implementation is wrong on average 50% of the time for all non monthly filers.  This module is wrong for a much
smaller subset of cases, but nonetheless, is not infallible.

In general, if you are more than one company, with multiple tax reporting periods, all unaligned to fiscal year with
filing periods other than monthly, this module *may* work by luck of date math, but best option is to raise an enterprise
support ticket.

