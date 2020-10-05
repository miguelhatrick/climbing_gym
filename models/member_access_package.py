# -*- coding: utf-8 -*-
import logging
import pdb
from datetime import datetime, timedelta, date, timezone
from typing import List
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MemberAccessPackage(models.Model):
    """Member Access package"""
    _name = 'climbing_gym.member_access_package'

    status_selection = [('pending', "Pending"), ('active', "Active"), ('completed', "Completed"),
                        ('cancel', "Cancelled")]

    # name = fields.Char('Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Member')

    obs = fields.Text('Observations')

    access_credits = fields.Integer('Amount of access credits', default=0, required=True)
    remaining_credits = fields.Integer('Remaining access credits', default=0, required=True)

    activated_date = fields.Datetime('Activation date', readonly=True)
    completed_date = fields.Datetime('Completed date', readonly=True)

    date_start = fields.Date('Package start date')
    date_finish = fields.Date('Package finish date')

    days_duration = fields.Integer('Package duration (Days)', default=0, required=True)
    locations = fields.Many2many('res.partner', string='Access Locations', readonly=False, required=True)
    product = fields.Many2one('product.product', string='Products linked')
    sale_order_line = fields.Many2one('sale.order.line', string='Linked Sale order line')
    access_package = fields.Many2one('climbing_gym.access_package', string='Linked access package', required=True)

    event_registrations = fields.One2many('event.registration', inverse_name='member_access_package_id',
                                          string='Events attended', readonly=True)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_revive(self):
        for _map in self:
            _map.activated_date = False
            _map.date_start = False
            _map.date_finish = False
            _map.completed_date = False

            _map.obs = "%s\r\n Revived on %s by %s" % (str(_map.obs or ''), datetime.now(), str(self.env.user.name))
            _map.state = 'pending'

    @api.multi
    def action_active(self):
        for _map in self:
            today = datetime.now().date()
            _map.activated_date = datetime.now()
            _map.date_start = today
            _map.date_finish = today + timedelta(days=_map.days_duration)
            _map.state = 'active'

    @api.multi
    def action_completed(self):
        for _map in self:
            _map.completed_date = datetime.now()
            _map.state = 'completed'
        # self.write({'state': 'completed'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.constrains('days_duration', 'access_credits')
    def _data_check_date(self):
        if self.days_duration <= 0:
            raise ValidationError('Duration must be > 0')
        elif self.access_credits <= 0:
            raise ValidationError('Credits must be > 0')
        else:
            pass

    @api.multi
    def update_status_cron(self):
        """Cron job to keep everything tidy"""
        arr = self.env['climbing_gym.member_access_package'].search(
            [('state', '=', "active")])
        _today = datetime.now().date()

        for _map in arr:
            _map.calculate_remaining_credits()
            if _map.date_finish < _today or _map.remaining_credits <= 0:
                _map.action_completed()

    def calculate_remaining_credits(self):
        # check for only confirmed or assisted by state
        self.remaining_credits = self.access_credits - len(
            self.event_registrations.filtered(lambda r: r.state == 'open' or r.state == 'done'))

        if self.state == 'pending' and self.remaining_credits != self.access_credits:
            self.action_active()

        if self.state != 'cancel' and self.remaining_credits < 1:
            self.action_completed()

        return self.remaining_credits

    def check_remaining_credits(self, event_registration):
        """Used to calculate if we have remaining credits for a new registration"""
        self.calculate_remaining_credits()
        _logger.info('calculating remaining credits ... -> %s' % self.remaining_credits)
        return self.remaining_credits + 1 if event_registration in self.event_registrations else 0

    @api.onchange('access_credits')
    def _onchange_access_credits(self):
        self.calculate_remaining_credits()

    @api.onchange('sale_order_line')
    def _onchange_sale_order_line(self):
        # db.set_trace()
        if len(self.sale_order_line):
            self.product = self.sale_order_line.product_id
        else:
            self.product = False

    @api.onchange('days_duration')
    def _onchange_days_duration(self):
        self.onchange_date_start()

    @api.onchange('date_start')
    def onchange_date_start(self):

        # pdb.set_trace()
        if self.date_start != False:
            self.date_finish = self.date_start + timedelta(days=self.days_duration)
        else:
            self.date_finish = False

    @api.onchange('access_package')
    def _onchange_access_package(self):
        _ap = self.access_package
        self.access_credits = _ap.access_credits
        self.days_duration = _ap.days_duration
        self.locations = [(6, 0, _ap.locations.ids)]

    def get_first_available(self, _member, _location):
        """Returns the first available Member access package for that location and member"""
        if not len(_member) or not len(_location):
            raise ValidationError('Partner or Location null in creation (get_first_available)')

        _logger.info('Looking for the first available member access package for ... -> %s' % _member.name)

        # search maps active
        _map_arr = self.env['climbing_gym.member_access_package'].search(
            [('state', '=', "active"), ('partner_id', '=', _member.id)]).filtered(
            lambda r, x=_location: x in r.locations)

        for _map in _map_arr:
            if _map.calculate_remaining_credits():
                return _map

        # search maps pending if not found
        _map_arr = self.env['climbing_gym.member_access_package'].search(
            [('state', '=', "pending"), ('partner_id', '=', _member.id)]).filtered(
            lambda r, x=_location: x in r.locations)

        for _map in _map_arr:
            if _map.calculate_remaining_credits():
                return _map;

        return False

    # @api.constrains('driver_id')
    # def _check_driver(self):
    #     FleetVehicle = self.env['fleet.vehicle']
    #     for record in self:
    #         if record.driver_id in self:
    #             vehicle_count = FleetVehicle.search_count(['driver_id', '=', record.driver_id])
    #             if vehicle_count > 0:
    #                 raise ValidationError("Driver already has a vehicle assigned")
    #

    #
    # @api.one
    # def link_event_reservation(self, event_reservation):
    #     # controlar si ya esta vinculado con otro map
    #
    #
    #     _map = self.env['climbing_gym.member_access_package'].search([('event_registration_id', '=', "event_reservation")])
    #
    #
    #     # recalcular creditos , ojo con los event.registration cancelados
    #
    #     # controlar que tenga creditos disponibles
    #     if self.days_duration <= 0:
    #         raise ValidationError('At least one duration must be > 0')
    #     elif self.access_credits <= 0:
    #         raise ValidationError('Credits must be > 0')
    #
    #
    #     # agregar el vinculo
    #     # actualizar los creditos
