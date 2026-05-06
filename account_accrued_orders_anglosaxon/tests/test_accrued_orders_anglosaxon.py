from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestAccruedOrdersAngloSaxon(TestSaleCommon):
    """Verify the accrued orders wizard routes counterpart accounts
    based on accrual_type context while perpetual (COGS) entries stay
    on the standard stock variation account.

    Stock closing pushes timing mismatches to stock variation.  Accruals
    resolve those mismatches, so the perpetual leg must use the same
    stock variation account — only the balance-sheet counterpart is
    overridden by this module.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        admin = cls.env.ref("base.user_admin")
        admin.write(
            {"company_ids": [(4, cls.env.company.id)]}
        )
        cls.env = cls.env(
            user=admin,
            context=dict(
                cls.env.context,
                allowed_company_ids=cls.env.company.ids,
            ),
        )

        cls.account_revenue = cls.company_data["default_account_revenue"]
        cls.account_expense = cls.company_data["default_account_expense"]

        cls.product_category = cls.env["product.category"].create(
            {
                "name": "Anglo-Saxon Test Category",
                "property_account_income_categ_id": cls.account_revenue.id,
                "property_account_expense_categ_id": cls.account_expense.id,
                "property_valuation": "real_time",
            }
        )
        cls.account_stock_variation = (
            cls.product_category.property_stock_valuation_account_id.account_stock_variation_id
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Anglo-Saxon Widget",
                "categ_id": cls.product_category.id,
                "invoice_policy": "order",
                "is_storable": True,
                "list_price": 100,
                "standard_price": 60,
                "uom_id": cls.uom_unit.id,
            }
        )

        cls.purchase_stock_accrual = cls.env["account.account"].create(
            {
                "name": "Purchase Stock Accrual",
                "code": "X21250",
                "account_type": "liability_current",
            }
        )
        cls.revenue_advance = cls.env["account.account"].create(
            {
                "name": "Revenue in Advance",
                "code": "X21260",
                "account_type": "liability_current",
            }
        )
        cls.delivered_in_advance = cls.env["account.account"].create(
            {
                "name": "Delivered in Advance",
                "code": "X21270",
                "account_type": "liability_current",
            }
        )

    def _put_in_stock(self, product, qty, unit_cost=None):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        receipt = warehouse.in_type_id
        cost = unit_cost or product.standard_price
        move = self.env["stock.move"].sudo().create(
            {
                "product_id": product.id,
                "location_id": receipt.default_location_src_id.id,
                "location_dest_id": receipt.default_location_dest_id.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "picking_type_id": receipt.id,
                "price_unit": cost,
                "value_manual": cost * qty,
            }
        )
        move._action_confirm()
        move._action_assign()
        move.picked = True
        move._action_done()
        return move

    def _configure_company(self):
        self.env.company.write(
            {
                "accrued_purchase_stock_account_id": (
                    self.purchase_stock_accrual.id
                ),
                "accrued_revenue_advance_account_id": (
                    self.revenue_advance.id
                ),
                "delivered_in_advance_account_id": (
                    self.delivered_in_advance.id
                ),
            }
        )

    def _create_wizard(self, model, order_ids, account, accrual_type=None):
        ctx = {
            "active_model": model,
            "active_ids": order_ids,
        }
        if accrual_type:
            ctx["accrual_type"] = accrual_type
        return (
            self.env["account.accrued.orders.wizard"]
            .sudo()
            .with_context(**ctx)
            .create(
                {
                    "account_id": account.id,
                    "date": fields.Date.today(),
                }
            )
        )

    # ------------------------------------------------------------------
    # Sale GDNI — perpetual uses stock variation, counterpart configured
    # ------------------------------------------------------------------

    def test_sale_gdni_perpetual_uses_stock_variation(self):
        """GDNI perpetual COGS lines must use stock_variation (where
        stock closing already pushed the timing mismatch), not a
        separate account."""
        self._configure_company()
        self._put_in_stock(self.product, 10)

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
            .sudo()
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 1,
                                "price_unit": 100,
                                "tax_ids": False,
                            }
                        )
                    ],
                }
            )
        )
        so.action_confirm()
        so.picking_ids.move_ids.write({"quantity": 1, "picked": True})
        so.picking_ids.button_validate()

        wizard = self._create_wizard(
            "sale.order", so.ids, self.delivered_in_advance, "gdni"
        )
        moves = self.env["account.move"].sudo().search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        sv_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertTrue(
            sv_lines,
            "GDNI perpetual must use stock variation",
        )

    def test_sale_gdni_exact_entry_structure(self):
        """Full journal entry verification for a GDNI accrual:
        counterpart uses delivered_in_advance, perpetual uses
        stock_variation."""
        self._configure_company()
        self._put_in_stock(self.product, 10)

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
            .sudo()
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 1,
                                "price_unit": 100,
                                "tax_ids": False,
                            }
                        )
                    ],
                }
            )
        )
        so.action_confirm()
        so.picking_ids.move_ids.write({"quantity": 1, "picked": True})
        so.picking_ids.button_validate()

        wizard = self._create_wizard(
            "sale.order", so.ids, self.delivered_in_advance, "gdni"
        )
        moves = self.env["account.move"].sudo().search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids.sorted("id")

        self.assertRecordValues(
            lines,
            [
                {
                    "account_id": self.account_revenue.id,
                    "debit": 0,
                    "credit": 100,
                },
                {
                    "account_id": self.delivered_in_advance.id,
                    "debit": 100,
                    "credit": 0,
                },
                {
                    "account_id": self.account_stock_variation.id,
                    "debit": 0,
                    "credit": 60,
                },
                {
                    "account_id": self.account_expense.id,
                    "debit": 60,
                    "credit": 0,
                },
                # Reversal
                {
                    "account_id": self.account_revenue.id,
                    "debit": 100,
                    "credit": 0,
                },
                {
                    "account_id": self.delivered_in_advance.id,
                    "debit": 0,
                    "credit": 100,
                },
                {
                    "account_id": self.account_stock_variation.id,
                    "debit": 60,
                    "credit": 0,
                },
                {
                    "account_id": self.account_expense.id,
                    "debit": 0,
                    "credit": 60,
                },
            ],
        )

    # ------------------------------------------------------------------
    # Sale GIND — perpetual uses stock variation
    # ------------------------------------------------------------------

    def test_sale_gind_perpetual_uses_stock_variation(self):
        """GIND perpetual lines must use stock_variation."""
        self._configure_company()

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
            .sudo()
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 1,
                                "tax_ids": False,
                            }
                        )
                    ],
                }
            )
        )
        so.action_confirm()
        inv = so._create_invoices()
        inv.sudo().action_post()

        wizard = self._create_wizard(
            "sale.order", so.ids, self.revenue_advance, "gind"
        )
        moves = self.env["account.move"].sudo().search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        sv_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertTrue(
            sv_lines,
            "GIND perpetual must use stock variation",
        )

    # ------------------------------------------------------------------
    # Purchase — perpetual uses stock variation
    # ------------------------------------------------------------------

    def test_purchase_perpetual_uses_stock_variation(self):
        """Purchase accrual perpetual lines must use stock_variation."""
        self._configure_company()

        po = self.env["purchase.order"].sudo().create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_qty": 5,
                            "product_uom_id": self.product.uom_id.id,
                            "price_unit": 80,
                            "tax_ids": False,
                        }
                    )
                ],
            }
        )
        po.button_confirm()

        pick = po.picking_ids
        pick.move_ids.write({"quantity": 5, "picked": True})
        pick.button_validate()

        wizard = self._create_wizard(
            "purchase.order", po.ids, self.purchase_stock_accrual, "grnb"
        )
        moves = self.env["account.move"].sudo().search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        sv_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertTrue(
            sv_lines,
            "Purchase perpetual must use stock variation",
        )

    # ------------------------------------------------------------------
    # Default account_id on wizard
    # ------------------------------------------------------------------

    def test_wizard_defaults_purchase_stock_accrual(self):
        """Wizard defaults to Purchase Stock Accrual for purchases."""
        self._configure_company()
        wizard = (
            self.env["account.accrued.orders.wizard"]
            .sudo()
            .with_context(
                active_model="purchase.order",
                active_ids=[1],
                accrual_type="grnb",
            )
            .new({})
        )
        self.assertEqual(wizard.account_id, self.purchase_stock_accrual)

    def test_wizard_defaults_revenue_advance_for_gind(self):
        """Wizard defaults to Revenue in Advance for GIND sales."""
        self._configure_company()
        wizard = (
            self.env["account.accrued.orders.wizard"]
            .sudo()
            .with_context(
                active_model="sale.order",
                active_ids=[1],
                accrual_type="gind",
            )
            .new({})
        )
        self.assertEqual(wizard.account_id, self.revenue_advance)

    def test_wizard_defaults_delivered_in_advance_for_gdni(self):
        """Wizard defaults to Delivered in Advance for GDNI sales."""
        self._configure_company()
        wizard = (
            self.env["account.accrued.orders.wizard"]
            .sudo()
            .with_context(
                active_model="sale.order",
                active_ids=[1],
                accrual_type="gdni",
            )
            .new({})
        )
        self.assertEqual(wizard.account_id, self.delivered_in_advance)
