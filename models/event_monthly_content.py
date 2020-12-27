# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import image_resize_images, image_resize_image, base64, logging
import pytz
from datetime import datetime

_logger = logging.getLogger(__name__)


class EventMonthlyContent(models.Model):
    """Month event content"""
    _name = 'climbing_gym.event_monthly_content'
    _description = 'Month event content'
    _inherit = ['mail.thread']

    name = fields.Char('Name', compute='_generate_name')

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]

    member_membership_id = fields.Many2one('climbing_gym.member_membership', string='Member membership', required=True,
                                           track_visibility=True)

    event_monthly_id = fields.Many2one('climbing_gym.event_monthly', string='Monthly event', required=True,
                                       track_visibility=True)

    event_monthly_group_id = fields.Many2one('climbing_gym.event_monthly_group', string='Monthly event group',
                                             track_visibility=True, required=True)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_confirm(self):
        _logger.info('Trying to confirm %s ...' % self.name)

        if self.event_monthly_group_id.require_active_membership:
            if self.member_membership_id.state != 'active':
                raise ValidationError("Membership is not active!")

        if self.event_monthly_group_id.require_active_medical_certificate:
            if not self.member_membership_id.partner_id.climbing_gym_medical_certificate_valid:
                raise ValidationError("Medical certificate missing / overdue")

        # Do we have space?
        self.event_monthly_id.calculate_current_available_seats()

        if self.event_monthly_id.seats_available <= 0:
            raise ValidationError("All available places have been taken")

        # TODO: Implement tag control

        self.write({'state': 'confirmed'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "EMC-%s" % (_map.id if _map.id else '')

    @api.onchange('event_monthly_id')
    def _onchange_event_monthly_id(self):

        """This disallows internal ID to be used on other member for the same membership"""
        if not self.member_membership_id or not self.event_monthly_id:
            return

        _id = self.id
        if isinstance(self.id, models.NewId):
            _id = -1 if not hasattr(self, '_origin_id') or not self._origin.id else self._origin.id

        _event_monthly_ids = self.sudo().env['climbing_gym.event_monthly_content'].search([
            ('member_membership_id', 'in', self.member_membership_id.ids),
            ('id', '!=', _id),
            ('event_monthly_id', '=', self.event_monthly_id.id),
            ('state', 'in', ["pending", "confirmed"])
            ])

        if len(_event_monthly_ids) > 0:
            raise ValidationError("Already inscribed in this event monthly!")

        if self.event_monthly_id:
            self.event_monthly_group_id = self.event_monthly_id.event_monthly_group_id
        else:
            self.event_monthly_group_id = None

    @api.onchange('event_monthly_group_id')
    def _onchange_event_monthly_group_id(self):
        res = {'domain': {'event_monthly_id': [('event_monthly_group_id', '=', self.event_monthly_group_id.id)]}}
        return res

    @api.multi
    def unlink(self):
        for _content in self:
            if _content.event_monthly_group_id.state == 'closed':
                raise UserError(_('You cannot delete a content of a closed group '))
        return super(EventMonthlyContent, self).unlink()
