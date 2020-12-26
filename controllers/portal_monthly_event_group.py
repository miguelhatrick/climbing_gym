# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
import pdb


from addons.website_form.controllers.main import WebsiteForm
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
            ('state', 'in', ['active'])
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

    @http.route(['/my/monthlyeventgroups/select', '/my/monthlyeventgroups/select/<int:group_id>'], type='http', auth="user", methods=['POST'], website=True)
    def portal_my_monthly_event_form(self, group_id,  **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        _errors = []

        _monthlyEventGroup = request.env['climbing_gym.event_monthly_group']
        _monthlyEventGroup_id = request.env['climbing_gym.event_monthly_group'].search([('id', '=', group_id)])

        if not _monthlyEventGroup_id or len(_monthlyEventGroup_id) == 0:
            _errors.append('Invalid monthly event')

        # check if the current partner can access this
        if not partner.climbing_gym_member_membership_membership_active:
            _errors.append('No active membership')

        if not partner.climbing_gym_medical_certificate_valid:
            _errors.append('No valid medical certificate')

        # check if is not over
        if not _monthlyEventGroup_id.state == 'active':
            _errors.append('Monthly event group is not active')

        values.update({
            'page_name': 'Select',
            'default_url': '/my/monthlyeventgroups/select',
            'error_arr': _errors,
            'errors_found': True if len(_errors) > 0 else False,
            'event_monthly_group': _monthlyEventGroup_id,
            'event_monthly_group_content': _monthlyEventGroup_id.event_monthly_ids.filtered(lambda _evc: _evc.state == 'active')
        })

        return request.render("climbing_gym.portal_my_event_monthly_group_form", values)



class CustomerPortalForm(WebsiteForm):
    @http.route('/website_form/shop.climbing_gym.event_monthly_group', type='http', auth="public", methods=['POST'],
                website=True)
    def website_form_event_monthly_group(self, **kwargs):
        partner = request.env.user.partner_id
        model_record = request.env.ref('climbing_gym.model_climbing_gym_event_monthly_group')

        # date
        issue_date = datetime.datetime.strptime(kwargs['issue_date'], "%Y-%m-%d").date()
        kwargs['issue_date'] = issue_date.strftime("%d/%m/%Y")

        try:
            data = self.extract_data(model_record, kwargs)
        except ValidationError as e:
            return json.dumps({'error_fields': e.args[0]})



        # borrar viejo

        # crear nuevo







        _medicalCertificate = request.env['climbing_gym.medical_certificate']

        _mc = _medicalCertificate.create({
                'partner_id': partner.id,
                'issue_date': issue_date,
                'doctor_name': kwargs['doctor_name'],
                'doctor_license': kwargs['doctor_license']
            }
        )

        if data['custom']:
            values = {
                'body': nl2br(data['custom']),
                'model': 'climbing_gym.medical_certificate',
                'message_type': 'comment',
                'no_auto_thread': False,
                'res_id': _mc.id,
            }
            request.env['mail.message'].sudo().create(values)

        if data['attachments']:
            _id = self.insert_attachment(model_record, _mc.id, data['attachments'])

        _at_ids = request.env['ir.attachment'].search([('res_model', '=', 'climbing_gym.medical_certificate'),
                                                             ('res_id', '=', _mc.id)])

        for _id in _at_ids:
            _mc.attachment_ids = [(4, _id.id)]

        return json.dumps({'id': _mc.id})