import base64
import io
from odoo import tools
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import PyPDF2
from PyPDF2 import PdfFileWriter, PdfFileReader
from pathlib import Path
from odoo.exceptions import UserError, ValidationError


class HrPayslipAttendance(models.Model):
    _inherit = 'hr.payslip'

    attendance_ids = fields.One2many('hr.attendance', 'employee_id', compute='_onchange_period_attendance',
                                     readonly=True, string='Attendance')

    overtime_ids = fields.One2many('airo.overtime.request', 'employee_id', compute='_onchange_period_attendance',
                                     readonly=True, string='Attendance')

    @api.depends('date_from', 'date_to')
    def _onchange_period_attendance(self):
        for rec in self:
            rec.attendance_ids = self.env['hr.attendance'].search([('check_in', '>=', rec.date_from), ('check_out', '<=', rec.date_to), ('employee_id' , '=', rec.employee_id.id)])
            rec.overtime_ids = self.env['airo.overtime.request'].search([('date_from', '>=', rec.date_from), ('date_to', '<=', rec.date_to), ('employee_id' , '=', rec.employee_id.id), ('state', '=', 'approved')])

    def _generate_pdf(self):
        mapped_reports = self._get_pdf_reports()
        attachments_vals_list = []
        generic_name = _("Payslip")
        template = self.env.ref('hr_payslip_attendance.mail_template_new_payslip_inherit', raise_if_not_found=False)
        for report, payslips in mapped_reports.items():
            for payslip in payslips:
                pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, payslip.id)

                if report.print_report_name:
                    pdf_name = safe_eval(report.print_report_name, {'object': payslip})
                else:
                    pdf_name = generic_name

                attachments_vals_list.append({
                    'name': pdf_name,
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': payslip._name,
                    'res_id': payslip.id
                })

        # create pdf attachment in database
        self.env['ir.attachment'].sudo().create(attachments_vals_list)
        file_dict = []
        # file_dict = {}
        if template:
            for att in attachments_vals_list:
                # get pdf attachment by ids
                file = self.env['ir.attachment'].search([('res_model', '=', att['res_model']), ('res_id', '=', att['res_id'])])
                if file:
                    for attach in file:
                        file_store = attach.store_fname
                        if file_store:
                            file_id = att['res_id']
                            file_name = attach.name
                            file_path = attach._full_path(file_store)
                            # file_dict["%s:%s:%s" % (file_store, file_name, file_id)] = dict(path=file_path, name=file_name, id=att['res_id'])
                            file_dict.append({
                                'path': file_path,
                                'name': file_name,
                                'id': file_id
                            })

            # encrypt pdf
            for rec in self:
                if rec == self[-1]:
                    for file_info in file_dict:
                        if file_info:
                            result = PdfFileWriter()
                            file1 = PdfFileReader(file_info["path"], strict=False, overwriteWarnings=False)
                            length = file1.numPages
                            for i in range(length):
                                pages = file1.getPage(i)
                                result.addPage(pages)
                            # password = not self.employee_id.pin and self.employee_id.work_email or self.employee_id.pin
                            password = rec.employee_id.work_email
                            result.encrypt(password)
                            output = io.BytesIO()
                            result.write(output)
                            test = base64.b64encode(output.getvalue())
                            output.close()

                            # generate encrypted pdf
                            data_id = rec.env['ir.attachment'].sudo().create({
                                'name': file_info["name"],
                                'type': 'binary',
                                'datas': test,
                                'res_model': file_info["name"],
                                'res_id': file_info["id"]
                            })

                            template.attachment_ids = [(6, 0, [data_id.id])]
                            template.send_mail(file_info["id"], email_layout_xmlid='mail.mail_notification_light')

    def action_payslip_done(self):
        invalid_payslips = self.filtered(lambda p: p.contract_id and (p.contract_id.date_start > p.date_to or (p.contract_id.date_end and p.contract_id.date_end < p.date_from)))
        if invalid_payslips:
            raise ValidationError(_('The following employees have a contract outside of the payslip period:\n%s', '\n'.join(invalid_payslips.mapped('employee_id.name'))))
        if any(slip.contract_id.state == 'cancel' for slip in self):
            raise ValidationError(_('You cannot valide a payslip on which the contract is cancelled'))
        if any(slip.state == 'cancel' for slip in self):
            raise ValidationError(_("You can't validate a cancelled payslip."))
        self.write({'state' : 'done'})

        line_values = self._get_line_values(['NET'])

        self.filtered(lambda p: not p.credit_note and line_values['NET'][p.id]['total'] < 0).write({'has_negative_net_to_report': True})
        self.mapped('payslip_run_id').action_close()
        # Validate work entries for regular payslips (exclude end of year bonus, ...)
        regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
        work_entries = self.env['hr.work.entry']
        for regular_payslip in regular_payslips:
            work_entries |= self.env['hr.work.entry'].search([
                ('date_start', '<=', regular_payslip.date_to),
                ('date_stop', '>=', regular_payslip.date_from),
                ('employee_id', '=', regular_payslip.employee_id.id),
            ])
        if work_entries:
            work_entries.action_validate()

        if self.env.context.get('payslip_generate_pdf'):
            if self.env.context.get('payslip_generate_pdf_direct'):
                self._generate_pdf()
            else:
                self.write({'queued_for_pdf': True})
                payslip_cron = self.env.ref('hr_payroll.ir_cron_generate_payslip_pdfs', raise_if_not_found=False)
                if payslip_cron:
                    payslip_cron._trigger()


    @api.model
    def _cron_generate_pdf(self):
        payslips = self.search([
            ('state', 'in', ['done', 'paid']),
            ('queued_for_pdf', '=', True),
        ])
        if not payslips:
            return
        BATCH_SIZE = 50
        payslips_batch = payslips[:BATCH_SIZE]
        payslips_batch._generate_pdf()
        payslips_batch.write({'queued_for_pdf': False})
        # if necessary, retrigger the cron to generate more pdfs
        if len(payslips) > BATCH_SIZE:
            self.env.ref('hr_payroll.ir_cron_generate_payslip_pdfs')._trigger()



