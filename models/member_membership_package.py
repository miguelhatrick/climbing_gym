# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MemberMembershipPackage(models.Model):
    """Member membership package"""
    _name = 'climbing_gym.member_membership_package'
    # _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]

    partner_id = fields.Many2one('res.partner', string='Member', required=True)
    member_membership_id = fields.Many2one('climbing_gym.member_membership', string='Member membership', required=True)

    obs = fields.Text('Observations')

    activated_date = fields.Datetime('Activation date', readonly=True)
    cancelled_date = fields.Datetime('Cancellation date', readonly=True)

    interval_length = fields.Integer('Interval length', default=1, required=True)
    interval_unit = fields.Selection(status_selection, string='Interval unit', required=True, default='years')

    product = fields.Many2one('product.product', string='Products linked')
    sale_order_line = fields.Many2one('sale.order.line', string='Linked Sale order line')
    membership_package = fields.Many2one('climbing_gym.membership_package', string='Linked member package',
                                         required=True)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.activated_date = False
            _map.cancelled_date = False

            _map.obs = "%s\r\n Revived on %s by %s" % (str(_map.obs or ''), datetime.now(), str(self.env.user.name))
            _map.state = 'pending'

    @api.multi
    def action_active(self):
        for _map in self:
            _map.activated_date = datetime.now()
            _map.state = 'active'

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'
            _map.cancelled_date = datetime.now()

    @api.constrains('interval_length', 'package_qty')
    def _data_check_date(self):
        if self.interval_length <= 0:
            raise ValidationError('Interval must be > 0')
        elif self.package_qty <= 0:
            raise ValidationError('Package quantity must be > 0')
        else:
            pass
