# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class airo_overtime_request(models.Model):
    _name = 'airo.overtime.request'
    _description = 'Employee overtime request'
    # _inherit = "res.users"

    _rec_name = 'name_seq'

    name_seq = fields.Char(string="Name", readonly=True, required=True, copy=False, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,  default=lambda self: self._get_default_name())
    date_from = fields.Datetime(string='From', required=True)
    date_to = fields.Datetime(string='To', required=True)
    overtime_reason = fields.Text(string='Reason')
    nbr_hours = fields.Float('Hours', compute='_get_nbr_hours')
    leave_manager_id = fields.Char(string='Approver', required=True)
    leave_manager = fields.Char(related='employee_id.leave_manager_id.name', readonly=True)
    leave_manager_email = fields.Char(related='employee_id.leave_manager_id.work_email')
    leave_type = fields.Selection([('rwd', 'Regular Work Days'), ('snwd', 'Special Non-Working Day'), ('regholiday', 'Regular Holiday'), ('regholidayot','Regular Holiday OT')], 'Overtime Type', default='rwd',
        readonly=False,  groups="hr.group_hr_user")
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To Approve'), ('approved', 'Approved'), ('rejected', 'Rejected')], 'State', default='draft',
        readonly=True)

    @api.model
    def _get_default_name(self):
        user = self.env['res.users'].has_group('hr.group_hr_user')
        if not user:
            return self.env['hr.employee'].search([('employee_id.user_id', '=', self.env.user.id)]).id

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from >= self.date_to:
            raise ValidationError('Date from should be less then Date To')

    @api.constrains('leave_manager_id')
    def check_approver(self):
        if self.leave_manager_id is None:
            raise ValidationError('Employee must have approver.')

    @api.depends('date_from', 'date_to', 'employee_id')
    def _get_nbr_hours(self):
        for req in self:
            # if req.date_to:
            #     req.date_from = req.date_to - timedelta(hours=2)
            # if req.date_from:
            #     req.date_to = req.date_from + timedelta(hours=2)

            if req.date_to and req.date_from:
                difference = req.date_to - req.date_from
                req.nbr_hours = float(difference.days) * 24 + (float(difference.seconds) / 3600)
            else:
                req.nbr_hours = 0.0
            if req.employee_id:
                req.leave_manager_id = req.leave_manager

    def to_confirm(self):
        self.write({'state': 'to_approve'})
        template = self.env.ref('airo_overtime_request.new_overtime_request_email_template', raise_if_not_found=False)
        print(template)
        for rec in self:
            template.send_mail(rec.id, email_layout_xmlid='mail.mail_notification_light')

    def to_reject(self):
        self.write({'state': 'rejected'})
        template = self.env.ref('airo_overtime_request.approval_overtime_request_email_template', raise_if_not_found=False)
        print(template)
        for rec in self:
            template.send_mail(rec.id, email_layout_xmlid='mail.mail_notification_light')

    def to_draft(self):
        self.write({'state': 'draft'})

    def is_approved(self):
        self.write({'state': 'approved'})
        template = self.env.ref('airo_overtime_request.approval_overtime_request_email_template', raise_if_not_found=False)
        for rec in self:
            template.send_mail(rec.id, email_layout_xmlid='mail.mail_notification_light')

    # def to_cancel(self):
    #     return {
    #             'name': 'Overtime Request',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             # 'view_id': False,
    #             'res_model': 'airo.overtime.request',
    #             'type': 'ir.actions.act_window',
    #             'target': 'main',
    #             'context': self._context,
    #             }

    @api.model
    def create(self, vals):
        if vals.get('name_seq', 'New') == 'New':
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('package.bundle.sequence') or 'New'
        result = super(airo_overtime_request, self).create(vals)
        return result

    @api.onchange('employee_id')
    def onchange_employee(self):
        user = self.env['res.users'].has_group('hr.group_hr_user')
        if not user:
            dom = [('employee_id.user_id', '=', self.env.user.id)]
            return {'domain': {'employee_id': dom}}


