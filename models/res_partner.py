# Copyright (C)
# Copyright 2020- (<http://www.a>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import pdb
from datetime import datetime

from odoo import fields, models, api


class ResPartner(models.Model):
    """Partner with birth date and other shit."""
    _inherit = "res.partner"

    birthdate_date = fields.Date("Birthdate")
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

    climbing_gym_medical_certificate_due_date = fields.Date('Medical Certificate due date', compute='update_certificate_due_date', store=True)
    climbing_gym_medical_certificate_valid = fields.Boolean('Medical certificate valid', compute='update_certificate_status')

    @api.one
    @api.depends('climbing_gym_medical_certificate_due_date')
    def update_certificate_status(self):
        _todaydate = datetime.now().date()
        self.climbing_gym_medical_certificate_valid = False

        if self.climbing_gym_medical_certificate_due_date is not False:
            self.climbing_gym_medical_certificate_valid = self.climbing_gym_medical_certificate_due_date >= _todaydate

    @api.one
    @api.depends('climbing_gym_medical_certificates')
    def update_certificate_due_date(self):
        self.climbing_gym_medical_certificate_valid = False
        self.climbing_gym_medical_certificate_due_date = None

        for _certificate in self.climbing_gym_medical_certificates:
            if _certificate.state != 'confirmed':
                continue
            #self.climbing_gym_medical_certificate_due_date = certi.due_date
            if self.climbing_gym_medical_certificate_due_date is False or self.climbing_gym_medical_certificate_due_date < _certificate.due_date:
                self.climbing_gym_medical_certificate_due_date = _certificate.due_date

        # pdb.set_trace()


    # FOR CALCULATING THE LAST CERT
    # last_id = self.env['table.name'].search([], order='id desc')[0].id



    # climbing_gym_image = fields.Binary("LAla Image", help="Select image here")

    #climbing_gym_association_id = fields.Date("AssociationDate")

