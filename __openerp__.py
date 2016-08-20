﻿{
    'name': 'Profit and Loss Report',
    'version': '9.0.1.0',
    'category': 'Accounting',
    'description': 
    """This modules adds a profit and loss report in detail. 

This module has been developed by Bernard Delhez, intern @ AbAKUS it-solutions, under the control of Valentin Thirion.
    """,
    'depends': ['account', 'account_report'],
    'data': [
        'wizard/profit_and_loss_view.xml',
        'reports/profit_and_loss.xml',
        ],
    'installable': True,
    'author': "Bernard DELHEZ, AbAKUS it-solutions SARL",
    'website': "http://www.abakusitsolutions.eu",
}
