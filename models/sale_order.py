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
                        self._create_access_package(line, _access_package)





    @api.one
    def _create_access_package(self, sale_order_line, access_package):
        # pdb.set_trace()

        # Access package can have its own multiplier.
        _map_qty = int(sale_order_line.product_uom_qty) * access_package.package_qty

        for x in range(0, _map_qty):
            _logger.info('Creating MAP ... -> %s' % (x + 1))

            _my_map = self.env['climbing_gym.member_access_package'].create({
                'partner_id': sale_order_line.order_id.partner_id.id,
                'obs': "Qty item %s/%s\r\n Created automatically after order confirmation" % (x + 1, _map_qty),
                'access_credits': access_package.access_credits,
                'remaining_credits': access_package.access_credits,
                'days_duration': access_package.days_duration,
                'locations': [(6, 0, access_package.locations.ids)],
                'product': sale_order_line.product_id.id,
                'sale_order_line': sale_order_line.id,
                'access_package': access_package.id,
                'state': 'pending',
            })

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
                        self._create_membership_package(line, _membership_package)

    @api.one
    def _create_membership_package(self, sale_order_line, _membership_package):
        # pdb.set_trace()

        # Access package can have its own multiplier.
        _mmp_qty = int(sale_order_line.product_uom_qty) * _membership_package.package_qty

        # look for an active membership
        mm_id = self.sudo().env['climbing_gym.member_membership'].search(
            [('partner_id', '=', sale_order_line.order_id.partner_id.id), ('state', 'in', ['active', 'overdue'])])

        # if none found look for inactive
        if len(mm_id) < 1:
            mm_id = self.sudo().env['climbing_gym.member_membership'].search(
                [('partner_id', '=', sale_order_line.order_id.partner_id.id), ('state', 'in', ['pending'])])

        if len(mm_id) < 1:
            _partner = sale_order_line.order_id.partner_id
            _message = 'No membership available for SALE SO-%s Partner: "%s"' % (sale_order_line.order_id.id, _partner.name)
            _message += '\r\n a MMP must be generated manually!'
            _logger.info(_message)

            self.env['mail.message'].create({
                'email_from': self.env.user.partner_id.email,  # add the sender email
                'author_id': self.env.user.partner_id.id,  # add  the creator id
                'model': 'mail.channel',  # model should be  mail.channel
                'type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,  # Leave this as it is
                'body': _message,  # here add message body
                'channel_ids': [
                    (4, self.env.ref('climbing_gym.channel_climbing_gym_group').id)],
                # This is the channel where you want to  send the message and all the users of this channel  will receive message
                'res_id': self.env.ref('climbing_gym.channel_climbing_gym_group').id,
                # here    add the channel you  created.
            })
            return

        _now = datetime.now()

        for x in range(0, _mmp_qty):
            _logger.info('Creating MMP ... -> %s' % (x + 1))

            _my_mmp = self.env['climbing_gym.member_membership_package'].create({
                'member_membership_id': mm_id[0].id,
                'obs': "Qty item %s/%s\r\n Created automatically after order confirmation" % (x + 1, _mmp_qty),
                'activated_date': _now,
                'product': sale_order_line.product_id.id,
                'sale_order_line': sale_order_line.id,
                'membership_package': _membership_package.id,
                'interval_length': _membership_package.interval_length,
                'interval_unit': _membership_package.interval_unit,
                'state': 'pending',
            })
            _my_mmp.action_active()

        # process_arr.append(['product': line.product_id, 'package': _access_package])
        # qty, product, client, order
        # line, _access_package, 'sale.order.line'
        # price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
        # taxes = \
        #    line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
        #                            partner=order.partner_shipping_id)['taxes']

        pass
