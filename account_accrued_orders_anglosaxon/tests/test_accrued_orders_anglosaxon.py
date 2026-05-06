from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestAccruedOrdersAngloSaxon(TestSaleCommon):
    """Verify the accrued orders wizard routes to the configured accounts
    depending on accrual_type context (gdni / gind) and order type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

        # --- accounts ---
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
        cls.undelivered_inventory = cls.env["account.account"].create(
            {
                "name": "Undelivered Inventory",
                "code": "X11250",
                "account_type": "asset_current",
            }
        )
        cls.delivered_in_advance = cls.env["account.account"].create(
            {
                "name": "Delivered in Advance",
                "code": "X21270",
                "account_type": "liability_current",
            }
        )
        cls.uninvoiced_inventory = cls.env["account.account"].create(
            {
                "name": "Uninvoiced Inventory",
                "code": "X11260",
                "account_type": "asset_current",
            }
        )

    def _put_in_stock(self, product, qty, unit_cost=None):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        receipt = warehouse.in_type_id
        cost = unit_cost or product.standard_price
        move = self.env["stock.move"].create(
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
                "undelivered_inventory_account_id": (
                    self.undelivered_inventory.id
                ),
                "delivered_in_advance_account_id": (
                    self.delivered_in_advance.id
                ),
                "uninvoiced_inventory_account_id": (
                    self.uninvoiced_inventory.id
                ),
            }
        )

    # ------------------------------------------------------------------
    # Sale GDNI — accrual_type = 'gdni'
    # ------------------------------------------------------------------

    def test_sale_gdni_uses_uninvoiced_inventory(self):
        """With accrual_type='gdni', perpetual COGS lines must hit
        uninvoiced_inventory, not undelivered_inventory or
        stock_variation."""
        self._configure_company()
        self._put_in_stock(self.product, 10)

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
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

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=so.ids,
                accrual_type="gdni",
            )
            .create(
                {
                    "account_id": self.delivered_in_advance.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        ui_lines = lines.filtered(
            lambda ln: ln.account_id == self.uninvoiced_inventory
        )
        self.assertTrue(
            ui_lines,
            "GDNI perpetual must use Uninvoiced Inventory",
        )
        self.assertFalse(
            lines.filtered(
                lambda ln: ln.account_id == self.account_stock_variation
            ),
            "Stock variation must not appear",
        )
        self.assertFalse(
            lines.filtered(
                lambda ln: ln.account_id == self.undelivered_inventory
            ),
            "Undelivered Inventory is for GIND, not GDNI",
        )

    def test_sale_gdni_exact_entry_structure(self):
        """Full journal entry verification for a GDNI accrual with
        accrual_type context: revenue + perpetual COGS + reversals."""
        self._configure_company()
        self._put_in_stock(self.product, 10)

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
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

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=so.ids,
                accrual_type="gdni",
            )
            .create(
                {
                    "account_id": self.delivered_in_advance.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids.sorted("id")

        self.assertRecordValues(
            lines,
            [
                # Revenue: CR Revenue, DR Delivered in Advance
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
                # COGS: DR Expense, CR Uninvoiced Inventory
                {
                    "account_id": self.uninvoiced_inventory.id,
                    "debit": 0,
                    "credit": 60,
                },
                {
                    "account_id": self.account_expense.id,
                    "debit": 60,
                    "credit": 0,
                },
                # Reversal — revenue
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
                # Reversal — COGS
                {
                    "account_id": self.uninvoiced_inventory.id,
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
    # Sale GIND — accrual_type = 'gind' (or absent)
    # ------------------------------------------------------------------

    def test_sale_gind_uses_undelivered_inventory(self):
        """With accrual_type='gind', perpetual lines must hit
        undelivered_inventory."""
        self._configure_company()

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
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
        inv.action_post()

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=so.ids,
                accrual_type="gind",
            )
            .create(
                {
                    "account_id": self.revenue_advance.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        ud_lines = lines.filtered(
            lambda ln: ln.account_id == self.undelivered_inventory
        )
        self.assertTrue(
            ud_lines,
            "GIND perpetual must use Undelivered Inventory",
        )
        self.assertFalse(
            lines.filtered(
                lambda ln: ln.account_id == self.uninvoiced_inventory
            ),
            "Uninvoiced Inventory is for GDNI, not GIND",
        )

    def test_sale_no_context_defaults_to_gind(self):
        """Without accrual_type context the wizard falls back to GIND
        accounts (undelivered_inventory)."""
        self._configure_company()

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
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
        inv.action_post()

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=so.ids,
            )
            .create(
                {
                    "account_id": self.revenue_advance.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        ud_lines = lines.filtered(
            lambda ln: ln.account_id == self.undelivered_inventory
        )
        self.assertTrue(
            ud_lines,
            "No accrual_type must fall back to Undelivered Inventory",
        )

    # ------------------------------------------------------------------
    # Purchase
    # ------------------------------------------------------------------

    def test_purchase_received_not_billed_uses_stock_variation(self):
        """Purchase perpetual lines must use the standard stock variation
        account (no override for purchases)."""
        self._configure_company()

        po = self.env["purchase.order"].create(
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

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="purchase.order",
                active_ids=po.ids,
            )
            .create(
                {
                    "account_id": self.purchase_stock_accrual.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids.sorted("id")

        if self.account_stock_variation:
            sv_lines = lines.filtered(
                lambda ln: ln.account_id == self.account_stock_variation
            )
            self.assertTrue(
                sv_lines,
                "Purchase must use stock variation account",
            )

    # ------------------------------------------------------------------
    # Default account_id on wizard
    # ------------------------------------------------------------------

    def test_wizard_defaults_purchase_stock_accrual(self):
        """Wizard account_id defaults to Purchase Stock Accrual for
        purchases."""
        self._configure_company()
        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="purchase.order", active_ids=[1]
            )
            .new({})
        )
        self.assertEqual(
            wizard.account_id,
            self.purchase_stock_accrual,
        )

    def test_wizard_defaults_revenue_advance_for_gind(self):
        """Wizard account_id defaults to Revenue in Advance for GIND
        sales (or when accrual_type is absent)."""
        self._configure_company()
        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=[1],
                accrual_type="gind",
            )
            .new({})
        )
        self.assertEqual(
            wizard.account_id,
            self.revenue_advance,
        )

    def test_wizard_defaults_delivered_in_advance_for_gdni(self):
        """Wizard account_id defaults to Delivered in Advance for GDNI
        sales."""
        self._configure_company()
        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=[1],
                accrual_type="gdni",
            )
            .new({})
        )
        self.assertEqual(
            wizard.account_id,
            self.delivered_in_advance,
        )

    # ------------------------------------------------------------------
    # Fallback: unconfigured accounts → stock variation
    # ------------------------------------------------------------------

    def test_sale_falls_back_to_stock_variation_when_unconfigured(self):
        """Without any company config, sale accruals must fall back to
        the stock variation account (standard sale_stock behaviour)."""
        self._put_in_stock(self.product, 10)

        so = (
            self.env["sale.order"]
            .with_context(tracking_disable=True)
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

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="sale.order",
                active_ids=so.ids,
                accrual_type="gdni",
            )
            .create(
                {
                    "account_id": self.account_expense.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        if self.account_stock_variation:
            self.assertTrue(
                lines.filtered(
                    lambda ln: ln.account_id
                    == self.account_stock_variation
                ),
                "Without config, must fall back to stock variation",
            )

    def test_purchase_falls_back_to_stock_variation_when_unconfigured(self):
        """Without company config, purchase accruals must use
        stock variation (standard behaviour)."""
        po = self.env["purchase.order"].create(
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

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(
                active_model="purchase.order",
                active_ids=po.ids,
            )
            .create(
                {
                    "account_id": self.account_expense.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(
            wizard.create_entries()["domain"]
        )
        lines = moves.line_ids

        if self.account_stock_variation:
            self.assertTrue(
                lines.filtered(
                    lambda ln: ln.account_id == self.account_stock_variation
                ),
                "Without config, must fall back to stock variation",
            )
