
{
    'name': 'Avalor Credit',
    'version': '13.0.1.0.5',
    'summary': 'Credito Financiero',
    'description': 'Integracion de APIs, Circulo de Credito',
    'category': 'Tools',
    'author': 'Jesus de Nazareth de La Cruz Limon',
    'maintainer': 'OGUM',
    'company': 'Ogum',
    'website': 'https://www.ogum.com.mx',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        "data/ir_sequence_data.xml",
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/api_credit.xml',
        'views/clip_preapproval.xml',
        'wizard/api_wizard.xml',
        'views/actividad_economica.xml',
        'views/account_loan.xml',
        'views/res_company.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'price': 120,
    'currency': 'USA',
    'installable': True,
    'application': True,
    'auto_install': False,
}
