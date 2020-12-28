# -*- coding: utf-8 -*-
import pdb

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import image_resize_images, image_resize_image, base64
import calendar


class EventWeekday(models.Model):
    """Weekdays used for auto populating the event table"""
    _name = 'climbing_gym.event_weekday'
    _description = 'Weekdays used for auto populating the event table'

    day_id = fields.Integer('Id for date operations')
    name = fields.Char('WeekdayName')

    localized_name = fields.Char(string='Localized weekday', compute='_get_localized_name')

    def _get_localized_name(self):
        for _wd in self:
            _wd.localized_name = calendar.day_name[_wd.day_id]
