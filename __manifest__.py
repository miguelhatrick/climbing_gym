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
    'version': '0.5',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'contacts', 'website', 'website_event', 'website_form', 'website_event_snippet_calendar', 'event_registration_partner_unique', 'portal'],

    # always loaded
    'data': [
        'data/cron_jobs.xml',
        'data/data_weekday.xml',
        'data/message_group.xml',
        'data/user_groups.xml',
        'data/medical_certificate_form.xml',

        'security/ir.model.access.csv',

        'views/portal/portal_my_documents.xml',
        'views/portal/portal_medical_certificate.xml',
        'views/portal/portal_member_access_package.xml',
        'views/portal/portal_member_membership.xml',
        'views/portal/portal_reservation.xml',
        'views/portal/event_website_sale_templates.xml',
        'views/portal/website_event_templates.xml',

        'views/access_package.xml',
        'views/event_event_views.xml',
        'views/event_generator.xml',
        'views/event_monthly.xml',
        'views/event_monthly_content.xml',
        'views/event_monthly_group.xml',
        'views/event_time_range.xml',
        'views/event_weekday.xml',
        'views/event_week_template.xml',
        'views/medical_certificate.xml',
        'views/membership.xml',
        'views/membership_package.xml',
        'views/member_access_package.xml',
        'views/member_membership.xml',
        'views/member_membership_package.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
