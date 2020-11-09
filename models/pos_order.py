# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime
import pdb
import logging

from addons_custom.climbing_gym.models.member_access_package import MemberAccessPackage
from addons_custom.climbing_gym.models.member_membership_package import MemberMembershipPackage
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    #
    # state = fields.Selection(
    #     [('draft', 'New'), ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced')],
    #     'Status', readonly=True, copy=False, default='draft')

    # lines = fields.One2many('pos.order.line', 'order_id', string='Order Lines', states={'draft': [('readonly', False)]},
    #                         readonly=True, copy=True)
    #
    # def action_pos_order_paid(self):
    #     if not self.test_paid():
    #         raise UserError(_("Order is not paid."))
    #     self.write({'state': 'paid'})
    #     return self.create_picking()

    # def action_pos_order_invoice(self):
    #     Invoice = self.env['account.invoice']
    #     for order in self:
    #         Invoice |= order._create_invoice()

    # def action_pos_order_done(self):
    #     return self._create_account_move_line()





    @api.multi
    def action_pos_order_paid(self):
        # pdb.set_trace()
        self.create_access_package()
        self.create_membership_package()

        return super(PosOrder, self).action_pos_order_paid()

    @api.multi
    def create_access_package(self):
        """Creates a new MAP based on the products"""

        ap_ids = self.sudo().env['climbing_gym.access_package'].search([('state', '=', "confirmed")])
        _logger.info('Begin MAP creation from POS SALE... ')

        for order in self:
            for line in order.lines:
                for _access_package in ap_ids:
                    if line.product_id in _access_package.products:
                        MemberAccessPackage.create_access_package(self, line, _access_package)
                        # self._create_access_package(line, _access_package)

    @api.multi
    def create_membership_package(self):
        """Creates a new MMP based on the products"""
        mp_ids = self.sudo().env['climbing_gym.membership_package'].search([('state', '=', "active")])

        _logger.info('Begin MMP creation from POS SALE...')

        for order in self:
            for line in order.lines:
                for _membership_package in mp_ids:
                    if line.product_id in _membership_package.products:
                        MemberMembershipPackage.create_membership_package(self, line, _membership_package)