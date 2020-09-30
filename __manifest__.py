# -*- coding: utf-8 -*-
{
    'name': "climbing_gym",

    'summary': """
       Climbing gym control control""",

    'description': """
        Climbing gym control system:
            - Day ticket
            - Monthly ticket with variations
            - Membership
    """,

    'author': "Miguel Hatrick",
    'website': "http://www.dacosys.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Administration',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'website_event', 'website_event_snippet_calendar', 'website_event_sale',
                'website_event_require_login', 'event_registration_partner_unique'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/association_type.xml',
        'views/event_generator.xml',
        'views/event_time_range.xml',
        'views/event_weekday.xml',
        'views/event_week_template.xml',
        'views/medical_certificate.xml',
        'views/res_partner.xml',
        'views/website_sale_address_b2b.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
