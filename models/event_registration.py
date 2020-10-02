import pdb

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    member_access_package_id = fields.Many2one('climbing_gym.member_access_package',
                                               string='Member access package linked')

    @api.constrains('member_access_package_id')
    def _check_available(self):
        for _er in self:
            # do we have it?
            if len(_er.member_access_package_id):
                if _er.member_access_package_id.check_remaining_credits(self) <= 0:
                    raise ValidationError('The member package has no more credits (EventRegistration)')
            else:
                pass

    @api.model
    def create(self, vals):

        _event = self.env['event.event'].search([('id', '=', vals['event_id'])])[0]
        _map = False

        # if event has a generator_id we are interested in this
        if len(_event.event_generator_id):
            _member = self.env['res.partner'].search([('id', '=', vals['partner_id'])])[0]
            _location = _event.address_id

            if not len(_member) or not len(_location):
                raise ValidationError('Partner or Location null in creation (EventRegistration)')

            _map = self.env['climbing_gym.member_access_package'].get_first_available(_member, _location)

            if not _map:
                raise ValidationError('The member package has no more credits / active packets (EventRegistration)')

            if _map.calculate_remaining_credits():
                vals['member_access_package_id'] = _map.id

        result = super(EventRegistration, self).create(vals)

        # recalculate after save
        if not _map:
            _map.calculate_remaining_credits()

        return result

    @api.multi
    def write(self, vals):
        result = super(EventRegistration, self).write(vals)

        # If linked and cancelled we want to recalculate the credits on the linked
        if len(self.member_access_package_id):
            if self.member_access_package_id.check_remaining_credits(self) <= 0:
                raise ValidationError('The member package has no more credits (EventRegistration)')

        return result
