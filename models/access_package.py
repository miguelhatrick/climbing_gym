# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64


class AccessPackage(models.Model):
    """Access packages for members"""
    _name = 'climbing_gym.access_package'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    access_credits = fields.Integer('Amount of access credits', default=0, required=True)
    days_duration = fields.Integer('Package duration (Days)', default=0, required=True)
    locations = fields.Many2many('res.partner', string='Access Locations', readonly=False, required=True)
    products = fields.Many2many('product.product', string='Products affected', required=True)

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

    @api.constrains('days_duration' ,'access_credits')
    def _data_check_date(self):
        if self.days_duration <= 0:
            raise ValidationError('At least one duration must be > 0')
        elif self.access_credits <= 0:
            raise ValidationError('Credits must be > 0')
        else:
            pass
