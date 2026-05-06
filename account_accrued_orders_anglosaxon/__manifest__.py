{
    "name": "Anglo-Saxon Accrued Orders",
    "version": "19.0.1.0.0",
    "summary": "Configurable accounts for Anglo-Saxon perpetual accrued orders",
    "author": "Graeme Gellatly",
    "website": "https://github.com/odoonz/works-in-belgium",
    "category": "Accounting",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "purchase",
        "sale_account_accountant",
        "purchase_accountant",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/sale_order_line_views.xml",
    ],
    "installable": True,
}
