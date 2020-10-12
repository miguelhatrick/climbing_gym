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
    _inherit = ['mail.thread']

    name = fields.Char('Name', compute='_generate_name')

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]
    interval_selection = [('days', "Days"), ('months', "Months"), ('years', "Years")]

    member_membership_id = fields.Many2one('climbing_gym.member_membership', string='Member membership', required=True, track_visibility=True)

    obs = fields.Text('Observations')

    activated_date = fields.Datetime('Activation date', readonly=True)
    cancelled_date = fields.Datetime('Cancellation date', readonly=True)

    product = fields.Many2one('product.product', string='Products linked')
    sale_order_line = fields.Many2one('sale.order.line', string='Linked Sale order line' , track_visibility=True)

    membership_package = fields.Many2one('climbing_gym.membership_package', string='Linked membership package',
                                         required=True, track_visibility=True)
    interval_length = fields.Integer('Interval length', required=True)
    interval_unit = fields.Selection(interval_selection, string='Interval unit', required=True)

    state = fields.Selection(status_selection, 'Status', default='pending' , track_visibility=True)

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

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "MMP-%s" % (_map.id if _map.id else '')

    @api.constrains('interval_length', 'package_qty')
    def _data_check_date(self):
        if self.interval_length <= 0:
            raise ValidationError('%s must be > 0' % 'Interval')
        elif not self.membership_package:
            raise ValidationError('%s must not be null' % 'Membership package')
        else:
            pass

    @api.onchange('sale_order_line')
    def _onchange_sale_order_line(self):
        if len(self.sale_order_line):
            self.product = self.sale_order_line.product_id
        else:
            self.product = False


    @api.onchange('membership_package')
    def _onchange_package(self):

        self.interval_length = self.membership_package.interval_length
        for _mmp in self:

            if _mmp.membership_package:
                _mmp.interval_unit = _mmp.membership_package.interval_unit
                _mmp.interval_length = _mmp.membership_package.interval_length
            else:
                _mmp.interval_length = -1
