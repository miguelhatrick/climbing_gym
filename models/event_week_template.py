# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64


class EventWeekTemplate(models.Model):
    """Week template for event creation"""
    _name = 'climbing_gym.event_week_template'

    name = fields.Char("Name", required=True)
    description = fields.Text()

    status_selection = [('active', "Active"), ('cancel', "Disabled")]

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

    ticket_product = fields.Many2one('product.product', string='Ticket product', required=True)

    seats_availability = fields.Integer("Maximum Attendees", required=True)

    state = fields.Selection(status_selection, 'Status', default='active')

    @api.multi
    def action_active(self):
        self.write({'state': 'active'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})


