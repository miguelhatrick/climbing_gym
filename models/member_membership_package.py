# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List

from dateutil.relativedelta import relativedelta

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

    member_membership_id = fields.Many2one('climbing_gym.member_membership', string='Member membership', required=True,
                                           track_visibility=True)

    obs = fields.Text('Observations')

    activated_date = fields.Datetime('Activation date', readonly=True)
    cancelled_date = fields.Datetime('Cancellation date', readonly=True)

    product = fields.Many2one('product.product', string='Products linked')

    sale_order = fields.Many2one('sale.order', compute='_get_sale_order')
    sale_order_line = fields.Many2one('sale.order.line', string='Linked Sale order line', track_visibility=True)

    pos_order = fields.Many2one('pos.order', string='POS order', compute='_get_pos_order')
    pos_order_line = fields.Many2one('pos.order.line', string='Linked POS order line', track_visibility=True)

    membership_package = fields.Many2one('climbing_gym.membership_package', string='Linked membership package',
                                         required=True, track_visibility=True)
    interval_length = fields.Integer('Interval length', required=True, track_visibility=True)
    interval_unit = fields.Selection(interval_selection, string='Interval unit', required=True, track_visibility=True)

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

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

            # recalculate member membership status
            _map.member_membership_id.calculate_due_date()

    @api.multi
    def action_cancel(self):
        for _map in self:
            _map.state = 'cancel'
            _map.cancelled_date = datetime.now()
            _map.member_membership_id.calculate_due_date()

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "MMP-%s" % (_map.id if _map.id else '')

    @api.constrains('interval_length')
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

    def get_interval_delta(self):
        _interval = {'days': 0, 'years': 0, 'months': 0, self.interval_unit: self.interval_length}

        return relativedelta(years=_interval['years'],
                             months=_interval['months'],
                             days=_interval['days'])

    def _get_sale_order(self):
        for _map in self:
            _map.sale_order = _map.sale_order_line.order_id if _map.sale_order_line is not False else False

    def _get_pos_order(self):
        for _map in self:
            _map.pos_order = _map.pos_order_line.order_id if _map.pos_order_line is not False else False

    @staticmethod
    def create_membership_package(self, sale_line, _membership_package):
        # pdb.set_trace()

        sale_order_line = False
        pos_order_line = False
        partner_id = False
        product_id = False
        product_qty = 0

        if isinstance(sale_line, type(self.sudo().env['sale.order.line'])):
            _logger.info('ORIGIN: Sale Order Line %d' % (sale_line.id))
            sale_order_line = sale_line
            pos_order_line = False
            partner_id = sale_line.order_id.partner_id
            product_id = sale_line.product_id
            product_qty = sale_line.product_uom_qty

        if isinstance(sale_line, type(self.sudo().env['pos.order.line'])):
            _logger.info('ORIGIN: POS Order Line %d' % (sale_line.id))
            sale_order_line = False
            pos_order_line = sale_line
            partner_id = sale_line.order_id.partner_id
            product_id = sale_line.product_id
            product_qty = sale_line.qty

        # Access package can have its own multiplier.
        _mmp_qty = int(product_qty) * _membership_package.package_qty

        # look for an active membership
        mm_id = self.sudo().env['climbing_gym.member_membership'].search(
            [('partner_id', '=', partner_id.id), ('state', 'in', ['active', 'overdue'])])

        # if none found look for inactive
        if len(mm_id) < 1:
            mm_id = self.sudo().env['climbing_gym.member_membership'].search(
                [('partner_id', '=', partner_id.id), ('state', 'in', ['pending', 'cancel'])])

        if len(mm_id) < 1:
            # _partner = sale_order_line.order_id.partner_id
            _message = 'No membership available for SALE %s Partner: "%s"' % (sale_line.order_id.name, partner_id.name)
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

            # TODO: Remove fixed string for channel, team and category search

            _ticket_values = {
                'company_id': None,
                'category_id': self.env['helpdesk.ticket.category'].sudo().search(
                    [('name', '=', 'Membresías / Cuotas')]).id,

                'partner_name': partner_id.name,
                'partner_email': partner_id.email,

                'description': _message,
                'name': 'No Membership available!',
                'attachment_ids': False,
                'channel_id': self.env['helpdesk.ticket.channel'].sudo().search([('name', '=', 'Web')]).id,
                'partner_id': partner_id.id,
                'team_id': self.env['helpdesk.ticket.team'].sudo().search([('name', '=', 'Secretaria')]).id,
            }
            new_ticket = self.env['helpdesk.ticket'].sudo().create(_ticket_values)

            return

        _now = datetime.now()

        for x in range(0, _mmp_qty):
            _logger.info('Creating MMP -> %d / %d' % (x + 1, _mmp_qty))

            _my_mmp = self.sudo().env['climbing_gym.member_membership_package'].create({
                'member_membership_id': mm_id[0].id,
                'obs': "Qty item %s/%s\r\n Created automatically after order confirmation" % (x + 1, _mmp_qty),
                'activated_date': _now,
                'product': product_id.id,
                'sale_order_line': sale_order_line.id if sale_order_line is not False else False,
                'pos_order_line': pos_order_line.id if pos_order_line is not False else False,
                'membership_package': _membership_package.id,
                'interval_length': _membership_package.interval_length,
                'interval_unit': _membership_package.interval_unit,
                'state': 'pending',
            })
            _my_mmp.action_active()

            _logger.info('Created MMP %d' % (_my_mmp.id))

        pass
