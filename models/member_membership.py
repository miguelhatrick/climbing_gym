# -*- coding: utf-8 -*-
import pdb
from datetime import datetime

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MemberMembership(models.Model):
    """Member membership"""
    _name = 'climbing_gym.member_membership'
    _description = 'Member membership'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('active', "Active"), ('overdue', "Overdue"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name', store=True)

    obs = fields.Text('Observations')
    member_internal_id = fields.Integer('Membership Internal ID', required=True, track_visibility=True)

    partner_id = fields.Many2one('res.partner', string='Member', required=True, index=True, track_visibility=True)
    membership_id = fields.Many2one('climbing_gym.membership', string='Membership', required=True, index=True,
                                    track_visibility=True)

    membership_start_date = fields.Date('Membership start date', track_visibility=True)
    canceled_date = fields.Datetime('Cancelled date', readonly=True, track_visibility=True)

    initial_due_date = fields.Date(string='Membership due date start',
                                   help='Due date to use to begin calculations. It can differ from membership due '
                                        'date in order to accommodate system migrations', track_visibility=True)
    current_due_date = fields.Date(string='Membership due date',
                                   help='Current due date is recalculated using the initial due date and the '
                                        'purchased membership packages',
                                   readonly=True, track_visibility=True)

    cancelled_reason = fields.Text('Cancellation reason', track_visibility=True)

    mmp_ids = fields.One2many('climbing_gym.member_membership_package', inverse_name='member_membership_id',
                              string='Membership packages', readonly=True)

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    @api.one
    @api.depends('partner_id', 'membership_id', 'member_internal_id')
    def _generate_name(self):
        # pdb.set_trace()
        if not self.membership_id or not self.member_internal_id or not self.partner_id:
            self.name = ''
        else:
            self.name = "(%s-%05d) %s" % (self.membership_id.code,
                                          self.member_internal_id,
                                          self.partner_id.name)



    @api.onchange('membership_id')
    def _get_last_membership_id(self):
        """Retrieves the last ID from the DB and does a + 1"""

        if type(self.id) != odoo.models.NewId:
            return

        _membership_ids = self.sudo().env['climbing_gym.member_membership'].search(
            [('membership_id', 'in', self.membership_id.ids)], limit=1, order='member_internal_id desc')

        self.member_internal_id = 1

        for _mem in _membership_ids:
            self.member_internal_id = _mem.member_internal_id + 1

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_active(self):
        for _map in self:
            # Check that we can activate it
            _map.onchange_identity_ids()

            today = datetime.now().date()

            if not _map.membership_start_date:
                _map.membership_start_date = today

            if not _map.initial_due_date:
                _map.initial_due_date = today

            # TODO: Calculate due date

            _map.state = 'active'

    @api.multi
    def action_cancel(self):
        for _map in self:
            today = datetime.now()
            _map.canceled_date = today
            _map.state = 'cancel'

    @api.onchange('membership_id', 'partner_id', 'state')
    def onchange_identity_ids(self):
        """This disallows two active memberships of the same kind to be active"""
        if not self.membership_id or not self.partner_id:
            return

        _id = -1 if type(self.id) == odoo.models.NewId else self.id
        _member_ids = self.sudo().env['climbing_gym.member_membership'].search([
            ('state', 'in', ['active', 'overdue']),
            ('partner_id', 'in', self.partner_id.ids),
            ('membership_id', 'in', self.membership_id.ids),
            ('id', '!=', _id)])

        if len(_member_ids) > 0:
            raise ValidationError("That contact is already an active member!")

    @api.onchange('member_internal_id', 'membership_id')
    def onchange_member_internal_id(self):
        """This disallows internal ID to be used on other member for the same membership"""
        if not self.membership_id or not self.member_internal_id:
            return

        _id = -1 if type(self.id) == odoo.models.NewId else self.id
        _member_ids = self.sudo().env['climbing_gym.member_membership'].search([
            ('membership_id', 'in', self.membership_id.ids),
            ('id', '!=', _id),
            ('member_internal_id', '=', self.member_internal_id)])

        if len(_member_ids) > 0:
            raise ValidationError("That internal ID has been used already!")

    # TODO : CALCULATE MEMBERSHIP DUE DATE

    # TODO : UPDATE DUE STATUS

    @api.multi
    def write(self, values):
        """Ensure that we have an updated name"""

        return super(MemberMembership, self).write(values)


    # @api.constrains('interval_length', 'package_qty')
    # def _data_check_date(self):
    #     if self.interval_length <= 0:
    #         raise ValidationError('Interval must be > 0')
    #     elif self.package_qty <= 0:
    #         raise ValidationError('Package quantity must be > 0')
    #     else:
    #         pass
