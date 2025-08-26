# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from odoo.exceptions import ValidationError, UserError
# from datetime import datetime
# import logging
# import pdb


class PlanningRole(models.Model):
    _inherit = "planning.role"

    factor_bu = fields.Float(
        string="Factor BU",
        default=1.0,
        help="Business Unit factor for this role, used in resource planning calculations.",
    )
    cost = fields.Monetary(
        string="Cost",
        help="Cost associated with this role, used for budgeting and financial planning.",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        help="Currency used for the cost of this role.",
        default=lambda self: self.env.company.currency_id,
    )
