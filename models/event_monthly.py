# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date, timezone
import pytz
from odoo import models, fields, api


class EventMonthly(models.Model):
    """Monthly events"""
    _name = 'climbing_gym.event_monthly'
    _description = 'List of events that can be reserved monthly'
    _inherit = ['mail.thread']

    months_choices = []
    years_choices = []
    currentYear = datetime.now().year

    for i in range(1, 13):
        months_choices.append((i, date(currentYear, i, 1).strftime('%B')))

    for i in range(currentYear, currentYear + 5):
        years_choices.append((i, str(i)))

    name = fields.Char("Name", required=True)
    title = fields.Char(string='Title for the event', required=True, default='')
    description = fields.Text(string='Description of the current template')

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Disabled")]

    event_monthly_group_id = fields.Many2one('climbing_gym.event_monthly_group', string='Monthly Group')

    event_ids = fields.One2many('event.event',
                                inverse_name='event_monthly_id',
                                string='Events linked',
                                readonly=False,
                                track_visibility=True)

    event_content_ids = fields.One2many('climbing_gym.event_monthly_content',
                                inverse_name='event_monthly_id',
                                string='Monthly events contents',
                                readonly=False,
                                track_visibility=True)


    location = fields.Many2one('res.partner', string='Event location', readonly=False, required=True)

    month = fields.Selection(months_choices, 'Month', required=True)
    year = fields.Selection(years_choices, 'Year', required=True)

    weekday = fields.Many2one('climbing_gym.event_weekday', string='Weekday', required=True)

    time_range = fields.Many2one(comodel_name='climbing_gym.event_time_range', string='Time ranges', required=True)

    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,
                               default=lambda self: self.env.user.tz or 'UTC')

    seats_availability = fields.Integer("Maximum Attendees", required=True)

    seats_available = fields.Integer("Available seats", compute='calculate_current_available_seats')

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_active(self):
        self.write({'state': 'active'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    def calculate_current_available_seats(self):
        for em in self:
            em.sudo().seats_available = em.seats_availability - em.event_content_ids.sudo().search_count([('event_monthly_id', '=', em.id), ('state', '=', 'confirmed')])