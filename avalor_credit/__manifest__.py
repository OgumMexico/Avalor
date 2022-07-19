
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
        'open_api',
        'base_api',
        'account_loan',
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

    'currency': 'USA',
    'installable': True,
    'application': True,
    'auto_install': False,
 "external_dependencies": {
        "python": [
            "numpy",
            "numpy-financial<=1.0.0",
            "bravado_core",
            "swagger_spec_validator",
            "bravado_core",
            "pyjks",
            "pyOpenSSL"
        ]},
}
