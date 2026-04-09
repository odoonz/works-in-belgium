from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestAccruedOrdersAngloSaxon(TestSaleCommon):
    """Verify the accrued orders wizard routes to the configured accounts."""

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
        cls.account_stock_valuation = (
            cls.product_category.property_stock_valuation_account_id
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
        cls.purchase_in_advance = cls.env["account.account"].create(
            {
                "name": "Purchase in Advance",
                "code": "X21270",
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
                "accrued_purchase_stock_account_id": self.purchase_stock_accrual.id,
                "accrued_revenue_advance_account_id": self.revenue_advance.id,
                "purchase_in_advance_account_id": self.purchase_in_advance.id,
                "undelivered_inventory_account_id": self.undelivered_inventory.id,
            }
        )

    # ------------------------------------------------------------------
    # Sale: GDNI (goods delivered not invoiced)
    # ------------------------------------------------------------------

    def test_sale_gdni_uses_undelivered_inventory(self):
        """GDNI perpetual adjustment must hit the configured
        undelivered_inventory_account_id, not stock_variation."""
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
            )
            .create(
                {
                    "account_id": self.revenue_advance.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(wizard.create_entries()["domain"])
        lines = moves.line_ids.sorted("id")

        undelivered_lines = lines.filtered(
            lambda ln: ln.account_id == self.undelivered_inventory
        )
        self.assertTrue(
            undelivered_lines,
            "Perpetual adjustment must use undelivered inventory account",
        )
        stock_var_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertFalse(
            stock_var_lines,
            "Stock variation account must not appear in accrual entries",
        )

    # ------------------------------------------------------------------
    # Sale: GIND (goods invoiced not delivered)
    # ------------------------------------------------------------------

    def test_sale_gind_uses_undelivered_inventory(self):
        """GIND perpetual adjustment must also hit undelivered inventory."""
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
        moves = self.env["account.move"].search(wizard.create_entries()["domain"])
        lines = moves.line_ids.sorted("id")

        undelivered_lines = lines.filtered(
            lambda ln: ln.account_id == self.undelivered_inventory
        )
        self.assertTrue(
            undelivered_lines,
            "GIND perpetual adjustment must use undelivered inventory account",
        )
        stock_var_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertFalse(
            stock_var_lines,
            "Stock variation account must not appear",
        )

    # ------------------------------------------------------------------
    # Purchase: received not billed
    # ------------------------------------------------------------------

    def test_purchase_received_not_billed_uses_purchase_in_advance(self):
        """Purchase main line must use the configured
        purchase_in_advance_account_id, not stock_variation."""
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
        moves = self.env["account.move"].search(wizard.create_entries()["domain"])
        lines = moves.line_ids.sorted("id")

        pia_lines = lines.filtered(
            lambda ln: ln.account_id == self.purchase_in_advance
        )
        self.assertTrue(
            pia_lines,
            "Purchase main line must use purchase in advance account",
        )
        stock_var_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertFalse(
            stock_var_lines,
            "Stock variation account must not appear in purchase accruals",
        )

    # ------------------------------------------------------------------
    # Default account_id on wizard
    # ------------------------------------------------------------------

    def test_wizard_defaults_purchase_stock_accrual(self):
        """Wizard account_id must default to Purchase Stock Accrual
        when opened from a purchase order."""
        self._configure_company()

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(active_model="purchase.order", active_ids=[1])
            .new({})
        )
        self.assertEqual(
            wizard.account_id,
            self.purchase_stock_accrual,
            "Default counterpart for purchases must be Purchase Stock Accrual",
        )

    def test_wizard_defaults_revenue_advance(self):
        """Wizard account_id must default to Revenue in Advance
        when opened from a sale order."""
        self._configure_company()

        wizard = (
            self.env["account.accrued.orders.wizard"]
            .with_context(active_model="sale.order", active_ids=[1])
            .new({})
        )
        self.assertEqual(
            wizard.account_id,
            self.revenue_advance,
            "Default counterpart for sales must be Revenue in Advance",
        )

    # ------------------------------------------------------------------
    # Fallback: unconfigured accounts → stock variation (base behaviour)
    # ------------------------------------------------------------------

    def test_sale_falls_back_to_stock_variation_when_unconfigured(self):
        """Without company config the sale wizard must fall back to the
        stock variation account (base sale_stock behaviour)."""
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
            )
            .create(
                {
                    "account_id": self.account_expense.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(wizard.create_entries()["domain"])
        lines = moves.line_ids

        stock_var_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertTrue(
            stock_var_lines,
            "Without config, sale accrual must fall back to stock variation",
        )

    def test_purchase_falls_back_to_stock_variation_when_unconfigured(self):
        """Without company config the purchase wizard must fall back to
        the stock variation account (base behaviour)."""
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
        moves = self.env["account.move"].search(wizard.create_entries()["domain"])
        lines = moves.line_ids

        stock_var_lines = lines.filtered(
            lambda ln: ln.account_id == self.account_stock_variation
        )
        self.assertTrue(
            stock_var_lines,
            "Without config, purchase accrual must fall back to stock variation",
        )

    # ------------------------------------------------------------------
    # Verify exact journal entry structure (GDNI)
    # ------------------------------------------------------------------

    def test_sale_gdni_exact_entry_structure(self):
        """Full journal entry verification for a GDNI sale accrual:
        revenue side + perpetual COGS adjustment + reversals."""
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
            )
            .create(
                {
                    "account_id": self.revenue_advance.id,
                    "date": fields.Date.today(),
                }
            )
        )
        moves = self.env["account.move"].search(wizard.create_entries()["domain"])
        lines = moves.line_ids.sorted("id")

        self.assertRecordValues(
            lines,
            [
                # Revenue accrual
                {
                    "account_id": self.account_revenue.id,
                    "debit": 0,
                    "credit": 100,
                },
                {
                    "account_id": self.revenue_advance.id,
                    "debit": 100,
                    "credit": 0,
                },
                # COGS perpetual adjustment (undelivered inventory)
                {
                    "account_id": self.undelivered_inventory.id,
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
                    "account_id": self.revenue_advance.id,
                    "debit": 0,
                    "credit": 100,
                },
                # Reversal — COGS perpetual
                {
                    "account_id": self.undelivered_inventory.id,
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
