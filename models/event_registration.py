import pdb
from datetime import datetime

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class EventRegistration(models.Model):
    """Extension of the event registration, checks for member credits in order to allow registration"""
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
        if not _map: # TODO: <-- is this ok?
            _map.calculate_remaining_credits()

        return result

    @api.multi
    def write(self, vals):
        result = super(EventRegistration, self).write(vals)

        # Fix for a bug when trying to update user id=16099
        for _map in self:
            # If linked and cancelled we want to recalculate the credits on the linked
            if len(_map.member_access_package_id):
                if _map.member_access_package_id.check_remaining_credits(_map) <= 0:
                    raise ValidationError('The member package has no more credits (EventRegistration)')

        return result

    @api.one
    def button_reg_cancel(self):
        """Extension of the event cancellation to reactivate the linked MAP"""
        result = super(EventRegistration, self).button_reg_cancel()

        if self.member_access_package_id:
            _map = self.member_access_package_id

            # Recalculate with the new canceled registration
            _map.calculate_remaining_credits()

            # If the event date is in the future and we have credits revive if completed.
            if self.event_begin_date > datetime.now() and _map.remaining_credits > 0:
                if _map.state == 'completed':

                    # If it's a single credit MAP we set it to pending. Else we leave the due date untouched
                    if _map.access_credits == 1:
                        _map.action_revive() # modifies due date
                    else:
                        _map.state = 'active'
