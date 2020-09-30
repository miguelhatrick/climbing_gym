# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64


class MedicalCertificate(models.Model):
    """Medical certificates of each climbing gym member"""
    _name = 'climbing_gym.medical_certificate'

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]


    partner_id = fields.Many2one(
        'res.partner', string='Climbing gym member', readonly=False, required=True)

    issue_date = fields.Date("Issue date", required=True)
    due_date = fields.Date("Due date", compute='_get_due_date', store=True, readonly=True)

    doctor_name = fields.Char(required=True)
    doctor_license = fields.Char(required=True)

    certificate_image = fields.Binary("Medical Certificate (Image)", help="Select image here")
    certificate_image_medium = fields.Binary("Medical Certificate (Image) Medium", help="Select image here")
    certificate_image_small = fields.Binary("Medical Certificate (Image) Small", help="Select image here")
    certificate_pdf_file = fields.Binary(string='PDF file', attachment=True)
    pdf_filename = fields.Char()

    obs = fields.Text()

    state = fields.Selection(status_selection, 'Status', default='pending')

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

    @api.constrains('certificate_pdf_file', 'pdf_filename')
    def get_data(self):
        if not self.pdf_filename: # No upload
            return
        if not self.pdf_filename.endswith('.pdf'):  # check if file pdf
            raise ValidationError('Cannot upload file different from .pdf file')
        else:
            pass

    @api.model
    def create(self, vals):
        image_resize_images(vals, big_name='certificate_image', medium_name='certificate_image_medium', small_name='certificate_image_small')
        result = super(MedicalCertificate, self).create(vals)
        # Update
        self.partner_id.update_certificate_due_date()
        return result

    @api.multi
    def write(self, vals):
        image_resize_images(vals, big_name='certificate_image', medium_name='certificate_image_medium', small_name='certificate_image_small')
        result = super(MedicalCertificate, self).write(vals)
        # Update
        self.partner_id.update_certificate_due_date()
        return result
