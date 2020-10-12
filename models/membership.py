# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Membership(models.Model):
    """Membership types"""
    _name = 'climbing_gym.membership'
    _description = 'Membership types'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]
    interval_selection = [('days', "Days"), ('months', "Months"), ('years', "Years")]

    name = fields.Char('Name', required=True, track_visibility=True)

    code = fields.Char('Code', required=True, size=3, track_visibility=True)

    description = fields.Text('Description')

    member_membership_ids = fields.One2many('climbing_gym.member_membership', inverse_name='membership_id',
                                            string='Member memberships', readonly=True)

    cancel_interval_length = fields.Integer(string='Interval length', default=1, required=True, track_visibility=True)
    cancel_interval_unit = fields.Selection(interval_selection, string='Interval unit', required=True, default='years', track_visibility=True)

    state = fields.Selection(status_selection, string='Status', default='active', track_visibility=True)

    @api.one
    @api.constrains('code', 'cancel_interval_length')
    def _check_code_length(self):
        if len(self.code) < 3:
            raise ValidationError('The code is too short.')
        elif self.cancel_interval_length < 1:
            raise ValidationError('%s must be > 0.' % 'Interval length')


    @api.multi
    def action_active(self):
        for _map in self:
            _map.state = 'active'

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'


    # TODO ADD CALCULATED FIELDS: MEMBERS, DUE MEMBERS, CANCELLED MEMBERS

    # TODO ADD RULES TO THE MEMBERSHIP

    # location_ids = fields.One2many(
    #      'res.partner', string='Location',
    #      readonly=False, track_visibility="onchange")

    # @api.depends('value')
    # def _value_pc(self):
    #    self.value2 = float(self.value) / 100
