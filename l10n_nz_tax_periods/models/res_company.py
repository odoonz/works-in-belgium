# Copyright 2023 Graeme Gellatly
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.tools import date_utils

class ResCompany(models.Model):

    _inherit = "res.company"

    def _get_tax_closing_period_boundaries(self, date):
        """ Returns the start and end date of the period in which the given date is included.
        Just use the dates given so it matches report. Ugly hack but needed as Odoo refuses
        to believe that any other country can have a tax year not commencing Jan 1.

        Because in NZ the tax year USUALLY starts on 1st April, but for GST reporting can actually be
        any 1st of month, we need to be able to override the end date of the tax period. For alternate periods
        you will need to override this method and set a tax_period_start context key (must be Date).
        """
        self.ensure_one()
        period_months = self._get_tax_periodicity_months_delay()
        if period_months == 1:
            # Shortcut for simple case
            end_date = date_utils.end_of(date, 'month')
            start_date = end_date + relativedelta(day=1, months=-period_months + 1)
            return start_date, end_date
        icp = self.env["ir.config_parameter"].sudo()
        vat_year_end = icp.get_param("account_reports.vat_year_end")
        if vat_period_start:
            month, day = vat_period_start.split("-")
            start_date, _date_to = date_utils.get_fiscal_year(
                date, day=int(day), month=int(month))
        else:
            start_date, _date_to = date_utils.get_fiscal_year(
                date, day=self.fiscalyear_last_day, month=int(self.fiscalyear_last_month))
        while True:
            end_date = start_date + relativedelta(months=period_months, days=-1)
            if start_date <= date <= end_date:
                return start_date, end_date
            start_date += relativedelta(months=period_months)

