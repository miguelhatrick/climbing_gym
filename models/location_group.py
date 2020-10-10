# -*- coding: utf-8 -*-

from odoo import models, fields, api


class location_group(models.Model):
    """I think i don't use this....."""
    _name = 'climbing_gym.location_group'
    _description = 'I think i don\'t use this.....'

    name = fields.Char()
    description = fields.Text()

    location_ids = fields.One2many(
         'res.partner', string='Location',
         readonly=False, track_visibility="onchange")

    # @api.depends('value')
    # def _value_pc(self):
    #    self.value2 = float(self.value) / 100
