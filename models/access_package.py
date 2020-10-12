# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64


class AccessPackage(models.Model):
    """Access packages for members"""
    _name = 'climbing_gym.access_package'
    _description = 'Access packages for members'
    _inherit = ['mail.thread']

    status_selection = [('pending', "Pending"), ('confirmed', "Confirmed"), ('cancel', "Cancelled")]

    name = fields.Char('Name', required=True, track_visibility=True)
    description = fields.Char('Description')
    access_credits = fields.Integer('Amount of access credits', default=0, required=True, track_visibility=True)
    days_duration = fields.Integer('Package duration (Days)', default=0, required=True, track_visibility=True)
    locations = fields.Many2many('res.partner', string='Access Locations', readonly=False, required=True)

    package_qty = fields.Integer(string='Package multiplier', required=True, default=1, track_visibility=True)
    products = fields.Many2many('product.product', string='Products affected', required=True, track_visibility=True)

    state = fields.Selection(status_selection, 'Status', default='pending', track_visibility=True)

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirmed'})
        # self. message_post(body='Activated package', subject='Package modification', message_type='notification', subtype=None, parent_id=False, attachments=None)

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        # self.message_post(body='Cancelled package', subject='Package modification', message_type='notification', subtype=None, parent_id=False, attachments=None)

    @api.model
    def create(self, vals):
        # self.message_post(body='Created package', subject='Package modification', message_type='notification', subtype=None, parent_id=False, attachments=None)
        result = super(AccessPackage, self).create(vals)
        return result

    @api.constrains('days_duration', 'access_credits', 'package_qty')
    def _data_check_date(self):
        if self.days_duration <= 0:
            raise ValidationError('At least one duration must be > 0')
        elif self.access_credits <= 0:
            raise ValidationError('%s must be > 0' % 'Credits')
        elif self.package_qty <= 0:
            raise ValidationError('must be > 0' % 'Package qty multiplier')
        else:
            pass
