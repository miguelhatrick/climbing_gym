# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from operator import itemgetter

from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo import fields, http, _
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortal(CustomerPortal):

    @http.route(['/my/monthlyeventgroups', '/my/monthlyeventgroups/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_monthly_event_groups(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()

        _partner_id = request.env.user.partner_id
        _member_membership = request.env['climbing_gym.member_membership']
        _member_membership_ids = _member_membership.sudo().search([('partner_id', '=', _partner_id.id)])

        _monthlyEventGroup = request.env['climbing_gym.event_monthly_group']

        domain = [
            ('state', 'in', ['active', 'closed'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Creation date'), 'order': 'create_date desc'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('climbing_gym.event_monthly_group', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        _count = _monthlyEventGroup.search_count(domain)

        # make pager
        pager = portal_pager(
            url="/my/monthlyeventgroups",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        _monthly_event_groups = _monthlyEventGroup.sudo().search(domain, order=sort_order, limit=self._items_per_page,
                                                                 offset=pager['offset'])

        request.session['my_monthlyeventgroups_history'] = _monthly_event_groups.ids[:100]

        test = _partner_id.climbing_gym_member_membership_membership_active

        values.update({
            'date': date_begin,
            'monthly_event_groups': _monthly_event_groups.sudo(),
            'cur_memberships': _member_membership_ids,
            'active_membership': _partner_id.climbing_gym_member_membership_membership_active,
            'cur_partner': _partner_id,
            'page_name': 'Monthly access to climbing wall',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/monthlyeventgroups',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("climbing_gym.portal_my_monthly_event_groups", values)

    @http.route(['/my/monthlyeventgroups/select', '/my/monthlyeventgroups/select/<int:group_id>'], type='http',
                auth="user", methods=['POST'], website=True)
    def portal_my_monthly_event_form(self, group_id, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        _errors = []

        _monthlyEventGroup = request.env['climbing_gym.event_monthly_group']
        _monthlyEventGroup_id = request.env['climbing_gym.event_monthly_group'].search([('id', '=', group_id)])

        if not _monthlyEventGroup_id or len(_monthlyEventGroup_id) == 0:
            _errors.append('Invalid monthly event group')

        # check if the current partner can access this
        if not partner.climbing_gym_member_membership_membership_active:
            _errors.append('No active membership')

        if not partner.climbing_gym_medical_certificate_valid:
            _errors.append('No valid medical certificate')

        # check if is not over
        if not _monthlyEventGroup_id.state == 'active':
            _errors.append('Monthly event group is not active')

        # check if is not over
        if not _monthlyEventGroup_id.get_registration_available(partner):
            _errors.append('Registration for this event is not available right now')

        _eventMonthlyContent = request.env['climbing_gym.event_monthly_content'].sudo()

        _monthlyEventContent_ids = _eventMonthlyContent.sudo().search([
            ('member_membership_id', 'in', partner.climbing_gym_member_membership_ids.ids),
            ('event_monthly_group_id', '=', _monthlyEventGroup_id.id)])

        values.update({
            'page_name': 'Select',
            'default_url': '/my/monthlyeventgroups/select',
            'error_arr': _errors,
            'errors_found': True if len(_errors) > 0 else False,
            'event_monthly_group': _monthlyEventGroup_id,
            'event_monthly_group_events': _monthlyEventGroup_id.event_monthly_ids.filtered(
                lambda _evc: _evc.state == 'active'),
            'registered_event_ids': [x.event_monthly_id.id for x in _monthlyEventContent_ids]

        })

        return request.render("climbing_gym.portal_my_event_monthly_group_form", values)


class CustomerPortalForm(WebsiteForm):
    @http.route('/website_form/shop.climbing_gym.event_monthly_group', type='http', auth="public", methods=['POST'],
                website=True)
    def website_form_event_monthly_group(self, **kwargs):
        partner = request.env.user.partner_id

        _eventMonthlyGroup = request.env['climbing_gym.event_monthly_group'].sudo()
        _eventMonthly = request.env['climbing_gym.event_monthly'].sudo()
        _eventMonthlyContent = request.env['climbing_gym.event_monthly_content'].sudo()

        _eventMonthlyGroup_id = _eventMonthlyGroup.search([('id', '=', kwargs['event_group_id'])])

        _tempIds = {k: v for k, v in kwargs.items() if k.startswith('emshift')}.values()
        _eventMonthly_ids = _eventMonthly.search([('id', 'in', list(_tempIds)), ('event_monthly_group_id', 'in', _eventMonthlyGroup_id.ids)])

        _weekend_count = len(_eventMonthly_ids.filtered(lambda pm: pm.weekday.id in [6, 7]))
        _weekday_count = len(_eventMonthly_ids) - _weekend_count

        _errors = []

        # perform checks
        if not _eventMonthlyGroup_id or len(_eventMonthlyGroup_id) == 0:
            _errors.append('Invalid monthly event group')

        # check if is not over
        if not _eventMonthlyGroup_id.state == 'active':
            _errors.append('Monthly event group is not active')

        # check if is not over
        if not _eventMonthlyGroup_id.get_registration_available(partner):
            _errors.append('Registration for this event is not available right now')

        # check if the current partner can access this
        if not partner.climbing_gym_member_membership_membership_active:
            _errors.append('No active membership')

        if not partner.climbing_gym_medical_certificate_valid:
            _errors.append('No valid medical certificate')

        if _weekend_count > _eventMonthlyGroup_id.weekend_reservations_allowed \
                or _weekday_count > _eventMonthlyGroup_id.weekday_reservations_allowed:
            _errors.append('Allowed reserve quantities surpassed')

        if len(_errors) > 0:
            return json.dumps({'error_fields': _errors[0]})

        try:
            _partnerMemberships_ids = partner.climbing_gym_member_membership_ids.filtered(
                lambda pm: pm.state == 'active')


            # Delete Old
            _monthlyEventContent_ids = _eventMonthlyContent.sudo().search([
                ('member_membership_id', 'in', partner.climbing_gym_member_membership_ids.ids),
                ('event_monthly_group_id', '=', _eventMonthlyGroup_id.id)])

            for _e in _monthlyEventContent_ids:
                _e.unlink()



            # create new

            for _eventMonthly_id in _eventMonthly_ids:

                _mec = _eventMonthlyContent.sudo().create({
                    'member_membership_id': _partnerMemberships_ids[0].id,
                    'event_monthly_id': _eventMonthly_id.id,
                    'event_monthly_group_id': _eventMonthlyGroup_id.id,
                    'state': 'pending'
                })

                # If we have a spot confirm it, first recalculate
                _eventMonthly_id.calculate_current_available_seats()
                if _eventMonthly_id.seats_available > 0:
                    _mec.state = 'confirmed'

        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})

        return json.dumps({'id': _mec.id})
