# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64
import pytz


class EventWeekTemplate(models.Model):
    """Week template for event creation"""
    _name = 'climbing_gym.event_week_template'
    _description = 'Week template for event creation'

    name = fields.Char("Name", required=True)
    title = fields.Char(string='Title for the event', required=True, default='')
    description = fields.Text(string='Description of the current template')

    status_selection = [('active', "Active"), ('cancel', "Disabled")]

    website = fields.Many2one(
        'website', string='Website', readonly=False, required=True)

    event_type_id = fields.Many2one(
        'event.type', string='Event type', readonly=False, required=True )

    location = fields.Many2one(
        'res.partner', string='Event location', readonly=False, required=True)

    organizer = fields.Many2one(
        'res.partner', string='Event Organizer', readonly=False, required=True)

    responsible = fields.Many2one(
        'res.partner', string='responsible', readonly=False, required=True)

    weekdays = fields.Many2many('climbing_gym.event_weekday', string='Weekdays', required=True)

    time_ranges = fields.Many2many(comodel_name='climbing_gym.event_time_range',
                                   relation='event_week_temp',
                                   column1='ewt_id',
                                   column2='etr_id',
                                   string='Time ranges', required=True)

    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,
                               default=lambda self: self.env.user.tz or 'UTC')

    ticket_product = fields.Many2one('product.product', string='Ticket product', required=True)

    seats_availability = fields.Integer("Maximum Attendees", required=True)

    state = fields.Selection(status_selection, 'Status', default='active')

    @api.multi
    def action_active(self):
        self.write({'state': 'active'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]
