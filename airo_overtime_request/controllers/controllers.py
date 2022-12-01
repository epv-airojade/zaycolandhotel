# -*- coding: utf-8 -*-
# from odoo import http


# class AiroOvertimeRequest(http.Controller):
#     @http.route('/airo_overtime_request/airo_overtime_request', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/airo_overtime_request/airo_overtime_request/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('airo_overtime_request.listing', {
#             'root': '/airo_overtime_request/airo_overtime_request',
#             'objects': http.request.env['airo_overtime_request.airo_overtime_request'].search([]),
#         })

#     @http.route('/airo_overtime_request/airo_overtime_request/objects/<model("airo_overtime_request.airo_overtime_request"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('airo_overtime_request.object', {
#             'object': obj
#         })
