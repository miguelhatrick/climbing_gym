# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MembershipPackage(models.Model):
    _name = 'climbing_gym.membership_package'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')

    membership_id = fields.Many2one('climbing_gym.membership', string='Membership', required=True)

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]
    interval_selection = [('days', "Days"), ('months', "Months"), ('years', "Years")]

    interval_length = fields.Integer('Interval length', default=1, required=True)
    interval_unit = fields.Selection(status_selection, string='Interval unit', required=True, default='years')

    package_qty = fields.Integer(string='Package multiplier', required=True, default=1)
    products = fields.Many2many('product.product', string='Products affected', required=True)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.constrains('interval_length', 'package_qty')
    def _data_check_date(self):
        if self.interval_length <= 0:
            raise ValidationError('Interval must be > 0')
        elif self.package_qty <= 0:
            raise ValidationError('Package quantity must be > 0')
        else:
            pass
