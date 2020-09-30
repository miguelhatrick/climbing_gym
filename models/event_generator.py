# -*- coding: utf-8 -*-
import calendar
import pdb
from datetime import datetime, timedelta, date, timezone

import pytz

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

        temps = self.templates
        num_days = calendar.monthrange(self.year, self.month)[1]
        days = [date(self.year, self.month, day) for day in range(1, num_days + 1)]

        for _day in days:
            for template in temps:
                weekdays = []
                for wd in template.weekdays:
                    weekdays.append(wd.day_id)

                if _day.weekday() in weekdays:
                    self.create_event(_day, template)

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def create_event(self, day, template):

        for hourpair in template.time_ranges:
            date_from = datetime.combine(day, datetime.min.time()) + timedelta(hours=hourpair.time_start)
            date_to = datetime.combine(day, datetime.min.time()) + timedelta(hours=hourpair.time_end)
            _tz = pytz.timezone(template.date_tz)

            date_from = date_from.replace(tzinfo=_tz).astimezone(pytz.utc)
            date_to = date_to.replace(tzinfo=_tz).astimezone(pytz.utc)

            pdb.set_trace()

            # DESCRIPTION? Location + Date + from -> to?
            event_name = '%s %s %s' %(template.location.name + str(timedelta(hours=hourpair.time_start)) + str(timedelta(hours=hourpair.time_end)))
            # ticket_sale_deadline = day.replace(tzinfo=_tz)

            event_id = self.env['event.event'].create({
                'is_online': False,
                'website_published': True,
                'forbid_duplicates': True,
                'seats_availability': 'limited',
                'website_require_login': True,
                'auto_confirm': True,
                'active': '1',
                'state': 'confirm',

                # 'event_type_id': 'physical',
                'date_tz': template.date_tz,
                'seats_max': template.seats_availability,
                'name': event_name,  # DESCRIPTION? Location + Date + from -> to?
                'date_begin': date_from,
                'date_end': date_to,

            })

            # pdb.set_trace()

            event_ticket_id = self.env['event.event.ticket'].create({
                'event_type_id': None,
                'price': 0.0,
                'deadline': day,
                'seats_availability': 'limited',
                'seats_reserved': 0,
                'seats_unconfirmed': 0,
                'seats_used': 0,

                'event_id': event_id.id,
                'product_id': template.ticket_product.id,
                'name': event_name,
                'seats_max': template.seats_availability,
                'seats_available': template.seats_availability,
                'organizer_id': template.organizer.id,
                'address_id': template.location.id,
            })
            #pdb.set_trace()
            #  'event_tickets_ids':