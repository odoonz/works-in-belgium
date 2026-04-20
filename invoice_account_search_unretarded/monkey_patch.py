# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Monkey patch reinstating the previous account.account.name_search body on
# the upstream class itself. We patch the method in place (rather than
# inheriting via _inherit and calling super()) so that any other module that
# inherits account.account and calls super().name_search() continues to work
# and ends up calling the patched implementation as its parent.

from odoo import api
from odoo.addons.account.models.account_account import AccountAccount
from odoo.fields import Domain


@api.model
@api.readonly
def name_search(self, name="", domain=None, operator="ilike", limit=100):
    move_type = self.env.context.get("move_type")
    if not move_type:
        # Bypass the patched body and call the original ORM implementation
        # directly. We can't use super() here because this function is not
        # bound to a class; the original method we replaced is the one that
        # added move_type handling on top of the ORM default.
        return super(AccountAccount, self).name_search(name, domain, operator, limit)

    partner = self.env.context.get("partner_id")
    suggested_accounts = (
        self._order_accounts_by_frequency_for_partner(
            self.env.company.id, partner, move_type
        )
        if partner
        else []
    )

    if not name and suggested_accounts:
        return [
            (record.id, record.display_name)
            for record in self.sudo().browse(suggested_accounts)
        ]

    digit_in_search_term = any(c.isdigit() for c in name)
    search_domain = Domain("display_name", "ilike", name) if name else []

    if digit_in_search_term:
        domain = Domain.AND([search_domain, domain])
    else:
        move_type_accounts = {
            "out": ["income"],
            "in": ["expense", "asset_fixed"],
        }
        allowed_account_types = move_type_accounts.get(move_type.split("_")[0])
        type_domain = (
            [("account_type", "in", allowed_account_types)]
            if allowed_account_types
            else []
        )
        domain = Domain.AND([search_domain, type_domain, domain])

    records = self.with_context(
        preferred_account_ids=suggested_accounts
    ).search_fetch(domain, ["display_name"], limit=limit)
    return [(record.id, record.display_name) for record in records]


AccountAccount.name_search = name_search
