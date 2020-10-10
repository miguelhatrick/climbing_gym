# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Membership(models.Model):
    _name = 'climbing_gym.membership'

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]

    name = fields.Char('Name', required=True)

    code = fields.Char('Code', required=True, size=3)

    description = fields.Text('Description')

    member_membership_ids = fields.One2many('climbing_gym.member_membership', inverse_name='membership_id',
                                            string='Member memberships', readonly=True)

    state = fields.Selection(status_selection, string='Status', default='active')

    @api.one
    @api.constrains('code')
    def _check_code_length(self):
        if len(self.code) < 3:
            raise ValidationError('The code is too short.')


    # TODO ADD CALCULATED FIELDS: MEMBERS, DUE MEMBERS, CANCELLED MEMBERS

    # TODO ADD RULES TO THE MEMBERSHIP

    # location_ids = fields.One2many(
    #      'res.partner', string='Location',
    #      readonly=False, track_visibility="onchange")

    # @api.depends('value')
    # def _value_pc(self):
    #    self.value2 = float(self.value) / 100
