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
    _inherit = ['mail.thread']

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

    # This is for the monthly events that can only be reserved once a month
    generate_monthly_reservation = fields.Boolean(string='Create monthly reservation', required=True, default=False)

    event_monthly_group_id = fields.Many2one(
        comodel_name='climbing_gym.event_monthly_group',
        string='Monthly reservation group',
        track_visibility=True)

    require_active_membership = fields.Boolean(string="Require active membership", required=True, default=True)
    require_active_medical_certificate = fields.Boolean(string="Require active medical certificate", required=True,
                                                        default=True)

    require_tags = fields.Many2many('res.partner.category', string='Required tags')

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    events = fields.One2many(
        'event.event',
        inverse_name='event_generator_id',
        string='Events generated',
        readonly=True,
        track_visibility=True)

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_generate(self):
        self.write({'state': 'generate'})

        self._generate()

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

        # Unlink Events
        ids = []
        for ev in self.events:
            ids.append(ev.id)

        for _my_id in ids:
            self.events = [(2, _my_id)]
            self.env["event.event"].search([('id', '=', _my_id)]).unlink()

        # Unlink event_month
        ids = []
        if self.event_monthly_group_id:
            for ev in self.event_monthly_group_id.event_monthly_ids:
                ids.append(ev.id)

            for _my_id in ids:
                self.event_monthly_group_id.event_monthly_ids = [(2, _my_id)]
                self.env["climbing_gym.event_monthly"].search([('id', '=', _my_id)]).unlink()

            _my_id = self.event_monthly_group_id.id
            self.event_monthly_group_id = [(2, _my_id)]
            self.env["climbing_gym.event_monthly_group"].search([('id', '=', _my_id)]).unlink()

    def _generate(self):
        temps = self.templates
        num_days = calendar.monthrange(self.year, self.month)[1]
        days = [date(self.year, self.month, day) for day in range(1, num_days + 1)]

        if self.generate_monthly_reservation:
            _emg_name = '%s  %s/%s' % (
                self.name,
                self.year,
                self.month)

            self.event_monthly_group_id = self.env['climbing_gym.event_monthly_group'].create({
                'name': _emg_name,
                'title': _emg_name,
                'description': '',
                'month': self.month,
                'year': self.year,
                'require_active_membership': self.require_active_membership,
                'require_active_medical_certificate': self.require_active_medical_certificate,
                'require_tags': self.require_tags
            })

        for _day in days:
            for template in temps:
                weekdays = []
                for wd in template.weekdays:
                    weekdays.append(wd.day_id)

                if _day.weekday() in weekdays:
                    self._create_event(_day, template)

    def _create_event(self, day, template):

        _weekday = self.env['climbing_gym.event_weekday'].search([('day_id', '=', day.weekday())])

        for hourpair in template.time_ranges:
            _tz = pytz.timezone(template.date_tz)

            date_from = _tz.localize(datetime.combine(day, datetime.min.time()) + timedelta(hours=hourpair.time_start))
            date_to = _tz.localize(datetime.combine(day, datetime.min.time()) + timedelta(hours=hourpair.time_end))
            time_from = ':'.join(str(timedelta(hours=hourpair.time_start)).split(':')[:2])
            time_to = ':'.join(str(timedelta(hours=hourpair.time_end)).split(':')[:2])

            # DESCRIPTION? Location + Date + from -> to?
            event_name = '%s %s %s' % (template.title, time_from.zfill(5), time_to.zfill(5))

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

            # if create event monthly is set
            if self.generate_monthly_reservation:

                _em = -1
                _event_monthly = self.sudo().env['climbing_gym.event_monthly']
                _events = _event_monthly.search([
                    ('event_monthly_group_id', '=', self.event_monthly_group_id.id),
                    ('year', '=', self.year),
                    ('month', '=', self.month),
                    ('weekday', '=', _weekday.id),
                    ('time_range', '=', hourpair.id),
                    ('location', '=', template.location.id)
                    ])

                if len(_events) > 0:
                    _em = _events[0]
                else:
                    _em_name = '%s %s %s %s' % (
                        template.title,
                        day.strftime('%A'),
                        time_from.zfill(5),
                        time_to.zfill(5))

                    _em_name_short = '%s %s %s' % (
                        day.strftime('%A'),
                        time_from.zfill(5),
                        time_to.zfill(5))

                    _em = self.env['climbing_gym.event_monthly'].create({
                        'name': _em_name,
                        'title': _em_name,
                        'description': '',
                        'event_monthly_group_id': self.event_monthly_group_id.id,
                        'location': template.location.id,
                        'month': self.month,
                        'year': self.year,
                        'weekday': _weekday.id,
                        'time_range': hourpair.id,
                        'date_tz': template.date_tz,
                        'seats_availability': template.seats_availability,
                    })

                # add the event
                _em.event_ids = [(4, myevent.id)]
