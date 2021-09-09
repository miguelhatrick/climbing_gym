# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import *
from dateutil.relativedelta import *

_logger = logging.getLogger(__name__)


class MemberMembership(models.Model):
    """Member membership"""
    _name = 'climbing_gym.member_membership'
    _description = 'Member membership'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('pending_payment', "Pending payment"), ('active', "Active"),
                        ('overdue', "Overdue"), ('cancel', "Cancelled")]

    # these are the valid states for a membership to consider it 'active'
    _valid_status_list = ['active', 'overdue', 'pending_payment']

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
            self.name = "%s-%05d - %s" % (self.membership_id.code,
                                          self.member_internal_id,
                                          self.partner_id.name)

    def get_state_valid(self):
        """
        Retrieves whatever if the current states should be considered as an 'Active'
        :return: bool
        """
        return self.state in self._valid_status_list

    @api.onchange('membership_id')
    def _get_last_membership_id(self):
        """Retrieves the last ID from the DB and does a + 1"""

        if isinstance(self.id, models.NewId):
            if self._origin.id:
                return
        elif self.id:
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
            _map.partner_id.update_main_membership()

    @api.multi
    def action_overdue(self):
        for _map in self:
            _map.state = 'overdue'

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
                _map.current_due_date = today

            _map.state = 'active'

            # Set the current as main membership for the contact
            _map.partner_id.update_main_membership()
            # _map.partner_id.climbing_gym_main_member_membership_id = _map

            # recalculate just in case
            _map.calculate_due_date()

    @api.multi
    def action_cancel(self):
        for _map in self:
            today = datetime.now()
            _map.canceled_date = today
            _map.state = 'cancel'
            _map.partner_id.update_main_membership()

    def calculate_status_due_date(self):
        # pdb.set_trace()
        if self.current_due_date:
            if self.current_due_date < datetime.now().date() and self.state == 'active':
                self.action_overdue()
            elif self.current_due_date >= datetime.now().date() and self.state == 'overdue':
                self.action_active()

    @api.onchange('initial_due_date')
    def _onchange_initial_due_date(self):
        self.calculate_due_date()

    @api.onchange('membership_id', 'partner_id', 'state')
    def onchange_identity_ids(self):
        """This disallows two active memberships of the same kind to be active"""
        if not self.membership_id or not self.partner_id:
            return

        # pdb.set_trace()

        _id = 0
        _logger.info('*******')
        _logger.info('onchange_identity_ids -> ID: %s' % self.id)
        _logger.info('*******')

        if isinstance(self.id, models.NewId):
            if not hasattr(self, '_origin'):
                return

            _id = -1 if not self._origin.id else self._origin.id
        else:
            _id = self.id

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

        _id = self.id
        if isinstance(self.id, models.NewId):
            _id = -1 if not hasattr(self, '_origin_id') or not self._origin.id else self._origin.id

        _member_ids = self.sudo().env['climbing_gym.member_membership'].search([
            ('membership_id', 'in', self.membership_id.ids),
            ('id', '!=', _id),
            ('member_internal_id', '=', self.member_internal_id)])

        if len(_member_ids) > 0:
            raise ValidationError("That internal ID has been used already!")

    @api.multi
    def calculate_due_date(self):
        """Calculates the due date of the membership and updates the corresponding fields"""
        for _mm in self:
            _mm._calculate_due_date()

    @api.one
    def _calculate_due_date(self):
        _due_date = self.initial_due_date

        for _mmp in self.mmp_ids.filtered(lambda r: r.state == 'active'):
            _due_date = _due_date + _mmp.get_interval_delta()

        self.current_due_date = _due_date
        self.calculate_status_due_date()

    @api.multi
    def write(self, vals):
        _result = super(MemberMembership, self).write(vals)

        return _result

    def cron_due_date(self):
        """Calculates the due date of the membership and updates the corresponding fields"""

        _logger.info('Begin cron_due_date Cron Job ... ')
        _now = datetime.now()

        _due_member_ids = self.sudo().env['climbing_gym.member_membership'].search([
            ('state', 'in', ['active']),
            ('current_due_date', '<', _now)])

        _logger.info('Found %d memberships due, processing ... ' % (len(_due_member_ids)))

        _due_member_ids.calculate_due_date()

    def update_name(self):
        self._generate_name()

    def cron_due_date_update_all(self):
        """Calculates the due date of the membership and updates the corresponding fields / All / Used once a day"""

        _logger.info('Begin cron_due_date Cron Job ... ')
        _now = datetime.now()

        _member_ids = self.sudo().env['climbing_gym.member_membership'].search([
            ('state', 'in', ['active', 'overdue'])])

        _logger.info('Found %d memberships, processing ... ' % (len(_member_ids)))

        _member_ids.calculate_due_date()

        for _mm in _member_ids:
            _mm.update_name()

    def cron_auto_cancel(self):
        """Calculates the auto cancel for the old memberships"""

        _logger.info('Begin cron_due_date Cron Job ... ')
        _now = datetime.now()

        _membership_ids = self.sudo().env['climbing_gym.membership'].search([
            ('state', 'in', ['active'])])

        for _m in _membership_ids:
            _logger.info('Processing membership type: %s ' % _m.name)

            _kill_date = datetime.now() - _m.get_cancellation_delta()

            _overdue_member_ids = self.sudo().env['climbing_gym.member_membership'].search([
                ('state', 'in', ['overdue']),
                ('current_due_date', '<', _kill_date),
                ('membership_id', '=', _m.id)
            ])

            _logger.info('Found %d memberships that need to be cancelled, processing ... ' % (len(_overdue_member_ids)))

            # _overdue_member_ids.action_cancel
            # _overdue_member_ids.cancelled_reason += '\r\nCancelled automatically due to long overdue'

            for _mm in _overdue_member_ids:
                # pdb.set_trace()

                _mm.action_cancel()
                _mm.cancelled_reason = '%s\r\nCancelled automatically due to long overdue' % (
                    _mm.cancelled_reason if _mm.cancelled_reason else '')

    # TODO: Mass email overdue members
    #
