# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta, date, timezone
import pytz


class EventMonthlyGroup(models.Model):
    """Monthly events group"""
    _name = 'climbing_gym.event_monthly_group'
    _description = 'Group of events that can be reserved monthly'
    _inherit = ['mail.thread']

    name = fields.Char("Name", required=True)
    title = fields.Char(string='Title for the description base', required=True, default='')
    description = fields.Text(string='Description of the current template')

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Disabled")]

    event_monthly_ids = fields.One2many('climbing_gym.event_monthly',
                                        inverse_name='event_monthly_group_id',
                                        string='Monthly events',
                                        readonly=False,
                                        track_visibility=True)

    months_choices = []
    years_choices = []
    currentYear = datetime.now().year

    for i in range(1, 13):
        months_choices.append((i, date(currentYear, i, 1).strftime('%B')))

    for i in range(currentYear, currentYear + 5):
        years_choices.append((i, str(i)))

    month = fields.Selection(months_choices, 'Month', required=True)
    year = fields.Selection(years_choices, 'Year', required=True)

    require_active_membership = fields.Boolean(string="Require active membership", required=True, default=True)

    require_active_medical_certificate = fields.Boolean(string="Require active medical certificate", required=True,
                                                        default=True)

    require_tags = fields.Many2many('res.partner.category', string='Required tags')

    event_content_ids = fields.One2many('climbing_gym.event_monthly_content',
                                        inverse_name='event_monthly_group_id',
                                        string='Monthly events contents',
                                        readonly=True,
                                        track_visibility=False)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})
        self.event_monthly_ids.action_pending()

    @api.multi
    def action_active(self):
        self.write({'state': 'active'})
        self.event_monthly_ids.action_active()

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        self.event_monthly_ids.action_cancel()


    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]
