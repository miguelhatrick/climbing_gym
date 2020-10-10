# -*- coding: utf-8 -*-
import calendar
import pdb
from datetime import datetime, timedelta, date, timezone

import pytz

from odoo import models, fields, api


class EventGenerator(models.Model):
    """Event generator that uses templates"""
    _name = 'climbing_gym.event_generator'
    _description = 'Event generator that uses templates'
    # _inherit = ['mail.thread']

    name = fields.Char("Name", required=True)
    description = fields.Text()

    status_selection = [('pending', "Pending"), ('generate', "Generated"), ('confirmed', "Confirmed"), ('cancel', "Canceled")]

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

    events = fields.One2many(
        'event.event', inverse_name='event_generator_id', string='Events generated',
        readonly=True, track_visibility="onchange")

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_generate(self):
        self.write({'state': 'generate'})

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
    def action_confirm(self):
        self.write({'state': 'confirmed'})
        for ev in self.events:
            ev.website_published = True
            ev.auto_confirm = True
            ev.state = 'confirm'
        # 'website_published': True,
        # 'active': '1',


    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

        ids = []
        for ev in self.events:
            ids.append(ev.id)

        # unlink all
        # self.events = [(5)]

        for myid in ids:
            self.events = [(2, myid)]
            self.env["event.event"].search([('id', '=', myid)]).unlink()


        # foreach event
        # 'website_published': false,
        # 'active': '0',

    def create_event(self, day, template):
        for hourpair in template.time_ranges:
            _tz = pytz.timezone(template.date_tz)

            date_from = _tz.localize(datetime.combine(day, datetime.min.time()) + timedelta(hours=hourpair.time_start))
            date_to = _tz.localize(datetime.combine(day, datetime.min.time()) + timedelta(hours=hourpair.time_end))

            # DESCRIPTION? Location + Date + from -> to?
            event_name = '%s %s %s' %(template.title,
                                      ':'.join(str(timedelta(hours=hourpair.time_start)).split(':')[:2]),
                                      ':'.join(str(timedelta(hours=hourpair.time_end)).split(':')[:2]))

            myevent = self.env['event.event'].create({
                'is_online': False,
                'website_published': False,
                'forbid_duplicates': True,
                'seats_availability': 'limited',
                'website_require_login': True,
                'auto_confirm': False,
                'active': True,
                'state': 'draft',

                # 'event_type_id': 'physical',
                'date_tz': template.date_tz,
                'seats_max': template.seats_availability,
                'name': event_name,  # DESCRIPTION? Location + Date + from -> to?
                'date_begin': date_from.astimezone(pytz.utc),
                'date_end': date_to.astimezone(pytz.utc),
                'organizer_id': template.organizer.id,
                'address_id': template.location.id,
                'event_type_id': template.event_type_id.id,
                'website_id': template.website.id

            })

            self.events = [(4, myevent.id)]
            # pdb.set_trace()

            event_ticket_id = self.env['event.event.ticket'].create({
                'event_type_id': None,
                'price': 0.0,
                'deadline': day,
                'seats_availability': 'limited',
                'seats_reserved': 0,
                'seats_unconfirmed': 0,
                'seats_used': 0,

                'event_id': myevent.id,
                'product_id': template.ticket_product.id,
                'name': event_name,
                'seats_max': template.seats_availability,
                'seats_available': template.seats_availability,

            })
            #pdb.set_trace()
            #  'event_tickets_ids':