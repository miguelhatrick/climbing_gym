# Copyright (C)
# Copyright 2020- (<http://www.a>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
import pdb
from datetime import datetime, timedelta

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Partner with birthdate and other shit."""
    _inherit = "res.partner"

    birthdate_date = fields.Date("Birthdate")

    health_insurance = fields.Char('Health insurance', required=False, size=50, track_visibility=True)
    health_insurance_number = fields.Char('Health insurance affiliate number', required=False, size=30, track_visibility=True)
    health_insurance_emergency_phone = fields.Char('Health insurance emergency phone', required=False, size=30, track_visibility=True)

    emergency_contact_name = fields.Char('Emergency contact', required=False, size=100, track_visibility=True)
    emergency_contact_relationship = fields.Char('Emergency contact relationship', required=False, size=30, track_visibility=True)
    emergency_contact_phone = fields.Char('Emergency contact phone', required=False, size=30, track_visibility=True)

    # climbing_gym_association_date = fields.Date("Association Date")
    climbing_gym_association_id = fields.Char("Association ID")

    climbing_gym_main_member_membership_id = fields.Many2one(
        'climbing_gym.member_membership', string='Main membership',
        readonly=False, track_visibility="onchange")

    climbing_gym_medical_certificates = fields.One2many(
        'climbing_gym.medical_certificate', inverse_name='partner_id', string='Medical Certificates',
        readonly=False, track_visibility=True)

    member_access_packages = fields.One2many(
        'climbing_gym.member_access_package', inverse_name='partner_id', string='Access Packages',
        readonly=True, track_visibility=True)

    climbing_gym_member_membership_ids = fields.One2many(
        'climbing_gym.member_membership', inverse_name='partner_id', string='Memberships',
        readonly=False, track_visibility="onchange")

    climbing_gym_member_membership_active = fields.Boolean(
        string='Current partner has an active membership',
        compute='_get_current_partner_membership_active')

    climbing_gym_member_membership_valid = fields.Boolean(
        string='Current partner has a VALID membership (overdue, active, pending payment)',
        compute='_get_current_partner_membership_valid')

    climbing_gym_medical_certificate_due_date = fields.Date(
        'Medical Certificate due date',
        compute='update_certificate_due_date',
        store=True,
        compute_sudo=True)

    climbing_gym_medical_certificate_valid = fields.Boolean(
        'Medical certificate valid',
        compute='update_certificate_status',
        compute_sudo=True)

    climbing_gym_medical_certificate_latest = fields.Many2one(
        'climbing_gym.medical_certificate',
        'Latest confirmed certificate',
        compute='_get_latest_certificate',
        compute_sudo=True)

    @api.one
    @api.depends('climbing_gym_medical_certificate_due_date')
    def update_certificate_status(self):
        _today_date = datetime.now().date()

        for _partner in self:
            _partner.climbing_gym_medical_certificate_valid = False

            if _partner.climbing_gym_medical_certificate_due_date is not False:
                _partner.climbing_gym_medical_certificate_valid = _partner.climbing_gym_medical_certificate_due_date >= _today_date

    @api.one
    @api.depends('climbing_gym_medical_certificates')
    def update_certificate_due_date(self):
        for _partner in self:

            _partner.climbing_gym_medical_certificate_valid = False
            _partner.climbing_gym_medical_certificate_due_date = None

            for _certificate in _partner.sudo().climbing_gym_medical_certificates:
                if _certificate.state != 'confirmed':
                    continue

                if _partner.climbing_gym_medical_certificate_due_date is False or _partner.climbing_gym_medical_certificate_due_date < _certificate.due_date:
                    _partner.climbing_gym_medical_certificate_due_date = _certificate.due_date

    def _get_current_partner_membership_active(self):
        for _partner in self:
            _partner.climbing_gym_member_membership_active = False

            for _membership in _partner.sudo().climbing_gym_member_membership_ids:
                if _membership.state == 'active':
                    _partner.climbing_gym_member_membership_active = True
                    break

    def _get_current_partner_membership_valid(self):
        for _partner in self:
            _partner.climbing_gym_member_membership_valid = False

            for _membership in _partner.sudo().climbing_gym_member_membership_ids:
                if _membership.get_state_valid():
                    _partner.climbing_gym_member_membership_valid = True
                    break

    def _get_latest_certificate(self):
        for _partner in self:
            _partner.climbing_gym_medical_certificate_latest = self.sudo().env['climbing_gym.medical_certificate']. \
                search([('partner_id', '=', _partner.id),
                        ('state', '=', 'confirmed')], order='issue_date desc', limit=1)

    def update_main_membership(self):
        """
        Updates the main membership based on status
        :return: None
        """
        _partners = self.sudo()

        for _partner in _partners:
            for _membership in _partner.climbing_gym_member_membership_ids:
                if _membership.get_state_valid():
                    _partner.climbing_gym_main_member_membership_id = _membership
                    return

            # if we got here, disable
            _partner.climbing_gym_main_member_membership_id = None

    def action_send_medical(self):
        self.cron_send_medical_certificate_due_date_alert(4)

    def cron_send_medical_certificate_due_date_alert(self, days_left):
        """Send an email to every partner which certificate is due in N days"""

        _logger.info('Begin cron_send_medical_certificate_due_date_alert Cron Job ... ')
        due_date = datetime.now().date() + timedelta(days=days_left)

        _partner_ids = self.sudo().env['res.partner'] \
            .search([('climbing_gym_medical_certificate_due_date', '=', due_date)])

        _logger.info('Found %d partners, processing ... ' % (len(_partner_ids)))

        for _partner_id in _partner_ids.filtered(lambda r: r.climbing_gym_medical_certificate_latest is not False):
            _partner_id.climbing_gym_medical_certificate_latest.send_due_warning_email()
