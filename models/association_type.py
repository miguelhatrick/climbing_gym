# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AssociationType(models.Model):
    """Kind of association a partner has to the climbing gym."""
    _name = 'climbing_gym.association_type'

    name = fields.Char()
    description = fields.Text()

    # @api.depends('value')
    # def _value_pc(self):
    #    self.value2 = float(self.value) / 100
