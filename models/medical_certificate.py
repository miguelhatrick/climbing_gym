# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64


class MedicalCertificate(models.Model):
    """Medical certificates of each climbing gym member"""
    _name = 'climbing_gym.medical_certificate'
    _description = 'Medical certificates of each climbing gym member'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', compute='_generate_name')

    partner_id = fields.Many2one('res.partner', string='Climbing gym member', readonly=False, required=True, track_visibility=True)

    issue_date = fields.Date("Issue date", required=True, track_visibility=True)
    due_date = fields.Date("Due date", compute='_get_due_date', store=True, readonly=True)

    doctor_name = fields.Char(required=True)
    doctor_license = fields.Char(required=True)

    attachment_ids= fields.Many2many('ir.attachment', 'medical_certificates_rel', 'medical_certificate_id', 'attachment_id', 'Attachments')

    obs = fields.Text()

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

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
