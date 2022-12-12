# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime

import odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import *
from dateutil.relativedelta import *
from lxml import etree

_logger = logging.getLogger(__name__)


class MemberMembership(models.Model):
    """Member membership request"""
    _name = 'climbing_gym.member_membership_request'
    _description = 'Member membership'
    _inherit = ['mail.thread']

    status_selection = [('draft', "Draft"), ('pending', "Pending"), ('accept', "Accepted"),
                        ('reject', "Rejected"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')

    date_of_birth = fields.Date('Date of birth', required=True,
                                track_visibility=True)

    obs = fields.Text('Observations', required=False)

    member_membership_id = fields.Many2one('climbing_gym.member_membership', string='Member Membership generated',
                                           index=True,
                                           track_visibility=True)

    partner_id = fields.Many2one('res.partner', string='Member', required=True, index=True, track_visibility=True)

    membership_id = fields.Many2one('climbing_gym.membership', string='Membership requested', required=True, index=True,
                                    track_visibility=True)

    attachment_ids = fields.Many2many('ir.attachment', 'membership_request_rel', 'membership_request_id',
                                      'attachment_id', 'Attachments')

    state = fields.Selection(status_selection, 'Status', default='draft', track_visibility=True)

    # these are the valid states for a membership to consider it 'active'
    _valid_status_list = ['accepted']

    _required_contact_data = ['main_id_number',
                              'afip_responsability_type_id',
                              'street',
                              'city',
                              'state_id',
                              'country_id',
                              'phone',
                              ]

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "MMR-%s" % (_map.id if _map.id else '')

    def get_state_valid(self):
        """
        Retrieves whatever if the current states should be considered as an 'Active'
        :return: bool
        """
        return self.state in self._valid_status_list

    @api.multi
    def action_revive(self):
        for _map in self:
            if len(_map.member_membership_id) > 0 and not _map.member_membership_id.get_state_valid():
                raise ValidationError("Can't revive the registration without reviving the linked member membership!")
                return

            _map.state = 'pending'
            _map.partner_id.update_main_membership()

    @api.multi
    def action_accept(self):
        for _map in self:

            if self.partner_id.climbing_gym_member_membership_valid:
                raise ValidationError("User is already a valid member!")

            if not self.check_contact_data_filled():
                raise ValidationError("Contact has not filled all required profile data!")

            if len(self.attachment_ids) == 0:
                raise ValidationError("Must attach an ID card photo")

            _map.state = 'accept'
            _map.create_membership()

    @api.multi
    def action_pending(self):
        for _map in self:
            _map.state = 'pending'

    @api.multi
    def action_reject(self):
        for _map in self:
            _map.state = 'reject'

    @api.multi
    def action_cancel(self):
        for _map in self:

            if _map.member_membership_id.get_state_valid():
                raise ValidationError("Can't cancel a registration without cancelling the linked member membership!")
                return

            _map.state = 'cancel'

    @api.onchange('partner_id')
    def onchange_identity_ids(self):
        """This disallows even creating a request when the member has an active membership"""
        if not self.partner_id:
            return

        _id = 0
        _logger.info('*******')
        _logger.info('onchange_identity_ids -> ID: %s' % self.id)
        _logger.info('*******')

        if self.partner_id.climbing_gym_member_membership_valid:
            raise ValidationError("User is already a member!")

    def create_membership(self):
        """
        This function will create a new membership.
        Used when the request is approved
        """

        if self.member_membership_id is not None and len(self.member_membership_id) > 0:
            raise ValidationError("Request already has a membership linked!")

        _logger.info('Creating Membership for -> %s' % self.partner_id.name)

        _mm_hand = self.sudo().env['climbing_gym.member_membership']

        _mm = _mm_hand.create({
            'partner_id': self.partner_id.id,
            'membership_id': self.membership_id.id,
            'obs': "Created automatically from request %s" % self.name,
            'member_internal_id': _mm_hand.get_next_membership_id(self.membership_id),
            'state': 'pending_payment'
        })

        self.member_membership_id = _mm

        _logger.info('Created MM %s' % _mm.name)

        _logger.info('Updated DOB')
        self.partner_id.birthdate_date = self.date_of_birth

    def check_contact_data_filled(self):
        return len(self.check_contact_unmet_fields()) == 0

    def check_contact_unmet_fields(self):
        result = []

        if self.partner_id is None or len(self.partner_id) == 0:
            result.append('partner_id')
            result.extend(self._required_contact_data)
            return result

        for attr in self._required_contact_data:
            val = getattr(self.partner_id, attr)

            if val is False or val is None or len(val) == 0:
                result.append(attr)

        return result

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(MemberMembership, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                               submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            sale_reference = doc.xpath("//field[@name='partner_id']")
            if sale_reference:
                sale_reference[0].set("string", "lalalal")
                sale_reference[0].addnext(etree.Element('label', {'string': 'Sale Reference Number'}))
                result['arch'] = etree.tostring(doc, encoding='unicode')

        return result
