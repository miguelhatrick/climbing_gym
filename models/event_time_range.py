# -*- coding: utf-8 -*-
import datetime
import pdb

from odoo import models, fields, api


class EventTimeRange(models.Model):
    """Weekdays used for auto populating the event table"""
    _name = 'climbing_gym.event_time_range'

    status_selection = [('active', "Active"), ('cancel', "Disabled")]

    name = fields.Char('Name', compute='_generate_name', store=True)

    time_start = fields.Float('Start time', required=True)
    time_end = fields.Float('End time', required=True)

    state = fields.Selection(status_selection, 'Status', default='active')

    @api.multi
    def action_active(self):
        self.write({'state': 'active'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.one
    @api.depends('time_start', 'time_end')
    def _generate_name(self):
        # pdb.set_trace()
        self.name = str(datetime.timedelta(hours=self.time_start)).rsplit(':', 1)[0] + ' - ' + str(datetime.timedelta(hours=self.time_end)).rsplit(':', 1)[0]
