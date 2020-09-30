# -*- coding: utf-8 -*-
from odoo import http

# class Climbing-gym(http.Controller):
#     @http.route('/climbing_gym/climbing_gym/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/climbing_gym/climbing_gym/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('climbing_gym.listing', {
#             'root': '/climbing_gym/climbing_gym',
#             'objects': http.request.env['climbing_gym.climbing_gym'].search([]),
#         })

#     @http.route('/climbing_gym/climbing_gym/objects/<model("climbing_gym.climbing_gym"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('climbing_gym.object', {
#             'object': obj
#         })
