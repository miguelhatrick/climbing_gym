from datetime import datetime
import pdb
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ProductExtension(models.Model):
    _inherit = 'product.product'

    climbing_gym_only_members = fields.Boolean(string='Only members', required=True, default=False)
    climbing_gym_only_active_members = fields.Boolean(string='Force active memberships', required=True, default=False)

    @api.onchange('climbing_gym_only_members')
    def _value_pc(self):
        if not self.climbing_gym_only_members:
            self.climbing_gym_only_active_members = False

    @api.onchange('climbing_gym_only_active_members')
    def _value_pc(self):
        if self.climbing_gym_only_active_members:
            self.climbing_gym_only_members = True
