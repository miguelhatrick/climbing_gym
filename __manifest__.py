# -*- coding: utf-8 -*-
{
    'name': "climbing_gym",

    'summary': """
       Climbing gym control control""",

    'description': """
        Climbing gym control system:
            - Day / shift ticket
            - Monthly ticket with variations
            - Membership
            - Medical records
    """,

    'author': "Miguel Hatrick",
    'website': "http://www.dacosys.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Administration',
    'version': '0.4',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'contacts', 'website_event', 'website_event_snippet_calendar', 'event_registration_partner_unique', 'portal'],

    # always loaded
    'data': [
        'data/user_groups.xml',
        'data/data_weekday.xml',
        'security/ir.model.access.csv',
        'data/member_access_package.xml',
        'views/access_package.xml',
        'views/association_type.xml',
        'views/custom_portal.xml',
        'views/event_event_views.xml',
        'views/event_generator.xml',
        'views/event_templates.xml',
        'views/event_time_range.xml',
        'views/event_website_sale_templates.xml',
        'views/event_weekday.xml',
        'views/event_week_template.xml',
        'views/medical_certificate.xml',
        'views/member_access_package.xml',
        'views/res_partner.xml',
        'views/website_sale_address_b2b.xml',
        'views/website_event_templates.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
