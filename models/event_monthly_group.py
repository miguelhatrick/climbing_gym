# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta, date, timezone
import pytz
from odoo.exceptions import ValidationError


class EventMonthlyGroup(models.Model):
    """Monthly events group"""
    _name = 'climbing_gym.event_monthly_group'
    _description = 'Group of events that can be reserved monthly'
    _inherit = ['mail.thread']

    name = fields.Char("Name", required=True, track_visibility=True)
    title = fields.Char(string='Title for the description base', required=True, default='', track_visibility=True)
    description = fields.Text(string='Description of the current template', track_visibility=True)

    status_selection = [('pending', "Pending"), ('active', "Active"), ('closed', "Closed"), ('cancel', "Disabled")]

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

    month = fields.Selection(months_choices, 'Month', required=True, track_visibility=True)
    year = fields.Selection(years_choices, 'Year', required=True, track_visibility=True)

    require_active_membership = fields.Boolean(string="Require active membership", required=True, default=True, track_visibility=True)

    require_active_medical_certificate = fields.Boolean(string="Require active medical certificate", required=True,
                                                        default=True, track_visibility=True)

    require_tags = fields.Many2many('res.partner.category', string='Required tags', track_visibility=True)

    weekday_reservations_allowed = fields.Integer(string='Reservations allowed for weekdays', default=1, required=True,
                                                  track_visibility=True)
    weekend_reservations_allowed = fields.Integer(string='Reservations allowed for weekends', default=1, required=True,
                                                  track_visibility=True)

    event_content_ids = fields.One2many('climbing_gym.event_monthly_content',
                                        inverse_name='event_monthly_group_id',
                                        string='Monthly events contents',
                                        readonly=True,
                                        track_visibility=False)

    event_content_ids_active = fields.One2many('climbing_gym.event_monthly_content',
                                                        string='Active contents',
                                                        compute='_get_event_content_ids_active')

    current_partner_event_content_ids = fields.One2many('climbing_gym.event_monthly_content',
                                                        string='Logged Partner Monthly events contents',
                                                        compute='_get_current_partner_event_content_ids')

    partner_group_tag = fields.Many2one('res.partner.category', string='Partner group defined by tag', track_visibility=True)

    register_start_date = fields.Datetime('Registration start date',track_visibility=True)
    register_start_date_partner_group_tag = fields.Datetime('Registration start date for partners defined by TAG',track_visibility=True)

    register_end_date = fields.Datetime('Registration end date', track_visibility=True)

    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,
                               default=lambda self: self.env.user.tz or 'UTC')

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    @api.constrains('register_start_date', 'register_start_date_partner_group_tag', 'partner_group_tag', 'register_end_date')
    def _check_available(self):
        for _er in self:
            if _er.register_start_date_partner_group_tag and not _er.register_start_date:
                raise ValidationError('You must set a register start date before a partner group register start date')
            else:
                if _er.register_start_date_partner_group_tag and not _er.partner_group_tag:
                    raise ValidationError('You need to define a partner group tag')
            if (_er.register_end_date and _er.register_start_date) and _er.register_end_date < _er.register_start_date:
                raise ValidationError('Registration end date cant be before start date')

            pass

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})
        self.event_monthly_ids.action_pending()

    @api.multi
    def action_active(self):
        self.write({'state': 'active'})
        self.event_monthly_ids.action_active()

    @api.multi
    def action_close(self):
        self.write({'state': 'closed'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        self.event_monthly_ids.action_cancel()

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    @api.one
    def _get_current_partner_event_content_ids(self):
        _partner_id = self.env.user.partner_id
        _member_membership = self.sudo().env['climbing_gym.member_membership']
        _member_membership_ids = _member_membership.search([('partner_id', '=', _partner_id.id)])
        self.current_partner_event_content_ids = self.event_content_ids.search([('member_membership_id', 'in', _member_membership_ids)])

    @api.one
    def _get_event_content_ids_active(self):

        _emc = self.sudo().env['climbing_gym.event_monthly_content']
        self.event_content_ids_active = _emc.search([('state', '=', 'confirmed'), ('event_monthly_group_id', '=', self.id)])

    @api.model
    def get_registration_available(self, _partner):

        for _self in self:
            _tz = pytz.timezone(_self.date_tz)
            _now = _tz.localize(datetime.now())

            if _self.register_end_date and _now >= pytz.utc.localize(_self.register_end_date):
                return False

            if _self.state != 'active':
                return False

            # if no dates exist
            if not _self.register_start_date and not _self.register_start_date_partner_group_tag:
                return True

            # It belongs to the partner group?
            if _self.partner_group_tag in _partner.category_id and _self.register_start_date_partner_group_tag:
                if _now >= pytz.utc.localize(_self.register_start_date_partner_group_tag):
                    return True
            else:
                if _now >= pytz.utc.localize(_self.register_start_date):
                    return True

            return False

    @api.model
    def get_registration_start_date(self, _partner):

        for _self in self:
            # if no dates exist
            if not _self.register_start_date and not _self.register_start_date_partner_group_tag:
                return ''

            _tz = pytz.timezone(_self.date_tz)

            # It belongs to the partner group?
            if _self.partner_group_tag in _partner.category_id and _self.register_start_date_partner_group_tag:
                return pytz.utc.localize(_self.register_start_date_partner_group_tag).astimezone(_tz).strftime("%Y/%m/%d, %H:%M:%S")
            else:
                return pytz.utc.localize(_self.register_start_date).astimezone(_tz).strftime("%Y/%m/%d, %H:%M:%S")

    @api.model
    def get_registration_end_date(self):
        for _self in self:
            if not _self.register_end_date:
                return ''

            _tz = pytz.timezone(_self.date_tz)

            _cd = pytz.utc.localize(_self.register_end_date).astimezone(_tz)

            return _cd.strftime("%Y/%m/%d, %H:%M:%S")
