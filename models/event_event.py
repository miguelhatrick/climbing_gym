# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class EventEvent(models.Model):
    """Extension of the class Event"""
    _inherit = 'event.event'

    event_generator_id = fields.Many2one('climbing_gym.event_generator', string='Climbing generator')

    event_monthly_id = fields.Many2one('climbing_gym.event_monthly',
                                       string='Monthly event linked')

    website_require_login = fields.Boolean(
        string='Require login for website registrations',
        help='If set, a user must be logged in to be able to register '
             'attendees from the website.',
    )