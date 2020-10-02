# -*- coding: utf-8 -*-

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
        if public_user and event.website_require_login:
            return request.env['ir.ui.view'].render_template(
                'website_event_require_login'
                '.modal_attendees_registration_login_required', {
                    'event_url': event.website_url,
                })
        return super(
            RequireLoginToRegister, self).registration_new(event, **post)




# class AutoSelectPartner(WebsiteEventController):
#
#     @http.route()
#     def registration_new(self, event, **post):
#         tickets = self._process_tickets_details(post)
#         availability_check = True
#         if event.seats_availability == 'limited':
#             ordered_seats = 0
#             for ticket in tickets:
#                 ordered_seats += ticket['quantity']
#             if event.seats_available < ordered_seats:
#                 availability_check = False
#         if not tickets:
#             return False
#         return request.env['ir.ui.view'].render_template("website_event.registration_attendee_details", {'tickets': tickets, 'event': event, 'availability_check': availability_check})
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
#         return list(registrations.values())
#
#     @http.route(['''/event/<model("event.event", "[('website_id', 'in', (False, current_website_id))]"):event>/registration/confirm'''], type='http', auth="public", methods=['POST'], website=True)
#     def registration_confirm(self, event, **post):
#         if not event.can_access_from_current_website():
#             raise werkzeug.exceptions.NotFound()
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
