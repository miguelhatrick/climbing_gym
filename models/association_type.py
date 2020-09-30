# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api


class AssociationType(models.Model):
    """Kind of association a partner has to the climbing gym."""
    _name = 'climbing_gym.association_type'

    name = fields.Char()
    description = fields.Text()

    #member_count = fields.Integer("Members", computed='_calculate_members')

    members = fields.One2many(
        'res.partner', inverse_name='climbing_gym_association_type', string='Members',
        readonly=False, track_visibility="onchange")

    # @api.one
    # @api.depends('members')
    # def _calculate_members(self):
    #    pdb.set_trace()
    #    self.member_count = len(self.employee_id)
    #    # self.member_count = self.env['res.partner'].search_count([('climbing_gym_association_type', '=', self.id)])



    # @api.depends('value')
    # def _value_pc(self):
    #    self.value2 = float(self.value) / 100
