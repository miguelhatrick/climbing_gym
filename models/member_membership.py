# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MemberMembership(models.Model):
    """Member membership"""
    _name = 'climbing_gym.member_membership'
    _description = 'Member membership'

    status_selection = [('pending', "Pending"), ('active', "Active"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name', store=True)

    obs = fields.Text('Observations')
    member_internal_id = fields.Text('Membership Internal ID', required=True)

    partner_id = fields.Many2one('res.partner', string='Member', required=True, index=True)
    membership_id = fields.Many2one('climbing_gym.membership', string='Membership', required=True, index=True)

    membership_start_date = fields.Datetime('Membership start date', readonly=True)
    canceled_date = fields.Datetime('Cancelled date', readonly=True)

    initial_due_date = fields.Datetime(string='Membership due date start', help='Due date to use to begin calculations. It can differ from membership due date in order to accomodate system migrations', readonly=True)
    current_due_date = fields.Datetime(string='Membership due date',help='Current due date is recalculated using the initial due date and the purchased membership packages', readonly=True)

    cancelled_reason = fields.Text('Cancellation reason')

    mmp_ids = fields.One2many('climbing_gym.member_membership_package', inverse_name='member_membership_id',
                              string='Membership packages', readonly=True)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.one
    @api.depends('partner_id', 'membership_id', 'member_internal_id')
    def _generate_name(self):
        # pdb.set_trace()
        self.name = "(%s-%s) %s" % (self.membership_id.code if self.membership_id else '',
                                    self.member_internal_id if self.member_internal_id else '',
                                    self.partner_id.name if self.partner_id else '')

    @api.multi
    def action_active(self):
        for _map in self:
            today = datetime.now()

            if not _map.membership_start_date:
                _map.membership_start_date = today

            if not _map.initial_due_date:
                _map.initial_due_date = today

            # TODO: Calculate due date

            # TODO: Deny two active memberships to the same partner

            _map.state = 'active'

    @api.multi
    def action_cancel(self):
        for _map in self:
            today = datetime.now()
            _map.canceled_date = today
            _map.cancelled_reason = 'Cancelled by %s' % (str(self.env.user.name))
            _map.state = 'cancel'


    # TODO : Verify that the internal ID is not used on other member for the same membership

    # TODO : CALCULATE MEMBERSHIP DUE DATE

    # TODO : UPDATE DUE STATUS

    # @api.constrains('interval_length', 'package_qty')
    # def _data_check_date(self):
    #     if self.interval_length <= 0:
    #         raise ValidationError('Interval must be > 0')
    #     elif self.package_qty <= 0:
    #         raise ValidationError('Package quantity must be > 0')
    #     else:
    #         pass
