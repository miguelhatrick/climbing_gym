# -*- coding: utf-8 -*-
import logging

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class MedicalCertificate(models.Model):
    """Medical certificates of each climbing gym member"""
    _name = 'climbing_gym.medical_certificate'
    _description = 'Medical certificates of each climbing gym member'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')

    partner_id = fields.Many2one('res.partner', string='Climbing gym member', readonly=False, required=True,
                                 track_visibility=True)

    issue_date = fields.Date("Issue date", required=True, track_visibility=True)
    due_date = fields.Date("Due date", compute='_get_due_date', store=True, readonly=True)

    doctor_name = fields.Char(required=True)
    doctor_license = fields.Char(required=True)

    attachment_ids = fields.Many2many('ir.attachment', 'medical_certificates_rel', 'medical_certificate_id',
                                      'attachment_id', 'Attachments')

    obs = fields.Text()

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    # TODO: Add Main identification number to use in the template

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.one
    @api.depends('issue_date')
    def _get_due_date(self):
        if False != self.issue_date:
            self.due_date = self.issue_date + relativedelta(years=1)

    @api.model
    def create(self, vals):
        result = super(MedicalCertificate, self).create(vals)
        # Update
        self.partner_id.update_certificate_due_date()
        return result

    @api.multi
    def write(self, vals):
        result = super(MedicalCertificate, self).write(vals)
        # Update
        self.partner_id.update_certificate_due_date()
        return result

    def _generate_name(self):
        # pdb.set_trace()
        for _map in self:
            _map.name = "MC-%s" % (_map.id if _map.id else '')

    def cron_send_due_date_alert(self, days_left):
        """Send an email to every partner which certificate is due in N days"""

        _logger.info('Begin send_due_date_alert Cron Job ... ')
        due_date = datetime.now().date() + timedelta(days=days_left)

        _certificate_ids = self.sudo().env['climbing_gym.medical_certificate'] \
            .search([('state', 'in', ['confirmed']), ('due_date', '=', due_date)])

        _logger.info('Found %d certificates, processing ... ' % (len(_certificate_ids)))

        _certificate_ids.send_due_warning_email()

    @api.multi
    def send_due_warning_email(self):

        for _mc in self:

            for user in _mc.partner_id:
                if not user.email:
                    _mc.message_post(
                        body=_("Cannot send Due date email to: user %s has no email address.") % user.name,
                        subject='Due date email',
                        message_type='notification',
                        subtype=None,
                        parent_id=False,
                        attachments=None)

            template = _mc.env.ref('climbing_gym.medical_certificate_due_date_reminder')
            current_diff = _mc.due_date - datetime.now().date()

            template_values = {
                'email_to': '${object.partner_id.email|safe}',
                'email_from': 'dont@reply.com',
                'model': 'climbing_gym.medical_certificate',
                'email_cc': False,

                'due_date': _('Due date: %s') % _mc.due_date,
                'days_to_due': current_diff.days,
                'partner_name': _mc.partner_id.name,
                'subject': _('Your medical certificate is due in %d days') % current_diff.days,
                'explanation': _('Your medical certificate due date is coming soon'),
                'title_1': _('Your medical certificate'),
                'go_review': _('Please go to https://shop.caba.org.ar/my/home and review it.'),

                'thanks': _('Thank you')

            }

            template.write(template_values)

            template.with_context(template_values).send_mail(_mc.id, force_send=True, raise_exception=True)
            _mc.message_post(body=_("Due date email sent to: %s") % _mc.partner_id.email,
                             subject='Due date email',
                             message_type='notification',
                             subtype=None,
                             parent_id=False,
                             attachments=None)
