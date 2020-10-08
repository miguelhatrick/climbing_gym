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

        return super(SaleOrder, self).action_confirm()

    @api.multi
    def create_access_package(self):
        """Creates a new MAP based on the products"""

        # pdb.set_trace()

        aps = self.env['climbing_gym.access_package'].search([('state', '=', "confirmed")])

        _logger.info('Begin MAM creation ... ')

        for order in self:
            for line in order.order_line:
                for _access_package in aps:
                    if line.product_id in _access_package.products:
                        self._create_access_package(line, _access_package)

    @api.one
    def _create_access_package(self, sale_order_line, access_package):
        # pdb.set_trace()

        # Access package can have its own multiplier.
        _map_qty = int(sale_order_line.product_uom_qty) * access_package.package_qty

        for x in range(0, _map_qty):
            _logger.info('Creating MAM ... -> %s' % (x + 1))

            myevent = self.env['climbing_gym.member_access_package'].create({
                'partner_id': sale_order_line.order_id.partner_id.id,
                'obs': "Qty item %s/%s\r\n Created automatically after order confirmation" % (x + 1, _map_qty),
                'access_credits': access_package.access_credits,
                'remaining_credits': access_package.access_credits,
                'days_duration': access_package.days_duration,
                'locations':  [(6, 0, access_package.locations.ids)],
                'product': sale_order_line.product_id.id,
                'sale_order_line': sale_order_line.id,
                'access_package': access_package.id,
                'state': 'pending',
        })

        # process_arr.append(['product': line.product_id, 'package': _access_package])
        # qty, product, client, order
        # line, _access_package, 'sale.order.line'
        # price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
        # taxes = \
        #    line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
        #                            partner=order.partner_shipping_id)['taxes']

        pass
