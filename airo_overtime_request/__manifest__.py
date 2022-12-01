# -*- coding: utf-8 -*-
{
    'name': "airo_overtime_request",
    'summary': 'Connect Attendance to Payslip',
    'description': """
        Overtime request with email notification base on user role.
    """,

    'author': "AiroJade Solutions Inc",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'calendar', 'resource'],

    # always loaded
    'data': [

        'views/views.xml',
        'data/package_bundle_sequence.xml',

        'security/overtime_request_security.xml',
        'security/ir.model.access.csv',
        'data/overtime_request_email_template.xml',
        'data/overtime_request_approval_template.xml'


    ],
    # only loaded in demonstration mode
    'demo': [],
    'css': [],
    'installable': True,
    'application': True,
    'sequence': -100,
    'auto_install': False,
    'license': 'OPL-1'
}
