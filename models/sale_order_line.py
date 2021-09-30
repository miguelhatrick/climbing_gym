from datetime import datetime
import pdb
import logging
from odoo import fields, models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLineExtension(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.constrains('product_id')
    def _validate_product_for_members(self):
        """
This function is used to block users from adding a product to a non member
        """
        if self.product_id.climbing_gym_only_members:
            # only members
            _partner_id = self.order_id.partner_id
            if _partner_id is None or not _partner_id.climbing_gym_member_membership_valid:
                raise ValidationError("Product only available for climbing gym members: %s\n %s is not a member" % (
                    self.product_id.name, _partner_id.name))

            if self.product_id.climbing_gym_only_active_members and not _partner_id.climbing_gym_member_membership_active:
                raise ValidationError(
                    "Product only available for ACTIVE climbing gym members: Product %s\nMembership: %s\nStatus: %s\nDue date %s" % (
                        self.product_id.name,
                        _partner_id.climbing_gym_main_member_membership_id.name,
                        _partner_id.climbing_gym_main_member_membership_id.state,
                        _partner_id.climbing_gym_main_member_membership_id.current_due_date))
