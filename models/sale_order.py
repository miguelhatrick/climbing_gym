# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime
import pdb
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        # pdb.set_trace()
        self.create_access_package()
        self.create_membership_package()

        return super(SaleOrder, self).action_confirm()

    @api.multi
    def create_access_package(self):
        """Creates a new MAP based on the products"""

        ap_ids = self.sudo().env['climbing_gym.access_package'].search([('state', '=', "confirmed")])
        _logger.info('Begin MAP creation ... ')

        for order in self:
            for line in order.order_line:
                for _access_package in ap_ids:
                    if line.product_id in _access_package.products:
                        self.sudo().env['climbing_gym.member_access_package'].create_access_package(self, line, _access_package )

    @api.multi
    def create_all_membership_package(self):
        """Creates all MMP based of all orders"""

        so_ids = self.sudo().env['sale.order'].search([('state', 'in', [
            "to invoice",
            "invoiced",
            "sale",
            "done"
        ])])

        for so in so_ids:
            so.create_membership_package()

    @api.multi
    def create_membership_package(self):
        """Creates a new MMP based on the products"""
        mp_ids = self.sudo().env['climbing_gym.membership_package'].search([('state', '=', "active")])

        _logger.info('Begin MMP creation ... ')

        for order in self:
            for line in order.order_line:
                for _membership_package in mp_ids:
                    if line.product_id in _membership_package.products:
                        self.sudo().env['climbing_gym.member_membership_package'].create_membership_package(self, line, _membership_package)


