# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from odoo import models, fields, api


class EventGenerator(models.Model):
    """Event generator using templates"""
    _name = 'climbing_gym.event_generator'

    name = fields.Char("Name", required=True)
    description = fields.Text()

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]

    months_choices = []
    years_choices = []
    currentYear = datetime.now().year

    for i in range(1, 13):
        months_choices.append((i, date(currentYear, i, 1).strftime('%B')))

    for i in range(currentYear, currentYear + 5):
        years_choices.append((i, str(i)))

    month = fields.Selection(months_choices, 'Month', required=True)
    year = fields.Selection(years_choices, 'Year', required=True)
    templates = fields.Many2many(
                                 comodel_name='climbing_gym.event_week_template',
                                 relation='event_generator_l',
                                 column1='eg_id',
                                 column2='ewt_id',

                                 string='Templates', required=True)
    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})


