# -*- coding: utf-8 -*-
import pdb

import babel.dates
import re
import werkzeug
import json

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import fields, http, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import content_disposition, request

from odoo.http import request, route
from odoo.addons.website_event.controllers.main import WebsiteEventController


class RequireLoginToRegister(WebsiteEventController):

    @route()
    def registration_new(self, event, **post):

        public_user = request.env.user == request.website.user_id
        # pdb.set_trace()
        if public_user and event.website_require_login:
            return request.env['ir.ui.view'].render_template(
                'climbing_gym'
                '.modal_attendees_registration_login_required', {
                    'event_url': event.website_url,
                })
        elif not public_user and event.website_require_login:
            event_registration = request.env['event.registration']
            _member = request.env.user.partner_id

            if event_registration.search_count([('partner_id', '=', _member.id), ('event_id', '=', event.id),
                                                ('state', 'in', ['open', 'done'])]) > 0:
                return request.env['ir.ui.view'].render_template(
                    'climbing_gym'
                    '.modal_attendees_registration_already_registered', {
                        'event_url': event.website_url,
                    })

            # check for credits
            _map = request.env['climbing_gym.member_access_package']
            if not _map.get_first_available(_member, event.address_id):
                return request.env['ir.ui.view'].render_template(
                    'climbing_gym'
                    '.modal_attendees_registration_credits_required', {
                        'event_url': event.website_url,
                    })

            ## CUSTOM FROM HERE
            if event.event_generator_id:

                tickets = self._process_tickets_details(post)
                if not tickets:
                    return False

                for n in tickets:
                    n['quantity'] = 1

                tickets = [tickets[0]]

                return request.env['ir.ui.view'].render_template("climbing_gym.registration_attendee_details",
                                                                 {'tickets': [tickets[0]], 'event': event,
                                                                  'availability_check': event.seats_available >= 1,
                                                                  'mymember': _member})

        return super(
            RequireLoginToRegister, self).registration_new(event, **post)

#
# class AutoSelectPartner(WebsiteEventController):
#
#     @http.route(['''/event/<model("event.event", "[('website_id', 'in', (False, current_website_id))]"):event>/registration/confirm'''],
#                 type='http', auth="public", methods=['POST'], website=True)
#     def registration_confirm(self, event, **post):
#         if not event.can_access_from_current_website():
#             raise werkzeug.exceptions.NotFound()
#
#         pdb.set_trace()
#
#         Attendees = request.env['event.registration']
#         registrations = self._process_registration_details(post)
#
#         for registration in registrations:
#             registration['event_id'] = event
#             Attendees += Attendees.sudo().create(
#                 Attendees._prepare_attendee_values(registration))
#
#         urls = event._get_event_resource_urls(Attendees.ids)
#         return request.render("website_event.registration_complete", {
#             'attendees': Attendees.sudo(),
#             'event': event,
#             'google_url': urls.get('google_url'),
#             'iCal_url': urls.get('iCal_url')
#         })
#
#     def _process_registration_details(self, details):
#         ''' Process data posted from the attendee details form. '''
#         registrations = {}
#         global_values = {}
#         for key, value in details.items():
#             counter, field_name = key.split('-', 1)
#             if counter == '0':
#                 global_values[field_name] = value
#             else:
#                 registrations.setdefault(counter, dict())[field_name] = value
#         for key, value in global_values.items():
#             for registration in registrations.values():
#                 registration[key] = value
#         # pdb.set_trace()
#         # details = {'1-name': 'miguel', '1-email': 'miguelhatrick@gmail.com', '1-phone': '', '1-ticket_id': '404'}
#         # registrations
#         # {'1': {'name': 'miguel', 'email': 'miguelhatrick@gmail.com', 'phone': '', 'ticket_id': '404'}}
#         # (Pdb)
#         # registrations.values()
#         # dict_values([{'name': 'miguel', 'email': 'miguelhatrick@gmail.com', 'phone': '', 'ticket_id': '404'}])
#         # (Pdb)
#         return list(registrations.values())
