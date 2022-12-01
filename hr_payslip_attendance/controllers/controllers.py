# -*- coding: utf-8 -*-
# from odoo import http


# class HrPayslipAttendance(http.Controller):
#     @http.route('/hr_payslip_attendance/hr_payslip_attendance', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_payslip_attendance/hr_payslip_attendance/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_payslip_attendance.listing', {
#             'root': '/hr_payslip_attendance/hr_payslip_attendance',
#             'objects': http.request.env['hr_payslip_attendance.hr_payslip_attendance'].search([]),
#         })

#     @http.route('/hr_payslip_attendance/hr_payslip_attendance/objects/<model("hr_payslip_attendance.hr_payslip_attendance"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_payslip_attendance.object', {
#             'object': obj
#         })
