from datetime import datetime
import pdb
import logging
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrderLineExtension(models.Model):
    _inherit = 'pos.order.line'

    @api.constrains('product_id')
    def _validate_product_for_members(self):
        """
This function is used to block users from adding a product to a non member
        """
        if self.product_id.climbing_gym_only_members:
            # only members
            _partner_id = self.order_id.partner_id
            if _partner_id is None or _partner_id.climbing_gym_main_member_membership_id is None or len(
                    _partner_id.climbing_gym_main_member_membership_id) == 0:
                raise UserError('Product only available for climbing gym members: %s\n %s is not a member' % (
                self.product_id.name, _partner_id.name))

            if self.product_id.climbing_gym_only_active_members and _partner_id.climbing_gym_main_member_membership_id.state not in [
                'active']:
                raise UserError(
                    'Product only available for ACTIVE climbing gym members: Product %s\nMembership: %s\nStatus: %s\nDue date %s' % (
                        self.product_id.name,
                        _partner_id.climbing_gym_main_member_membership_id.name,
                        _partner_id.climbing_gym_main_member_membership_id.state,
                        _partner_id.climbing_gym_main_member_membership_id.due_date))
