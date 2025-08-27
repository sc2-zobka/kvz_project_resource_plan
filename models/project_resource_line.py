# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError


class ProjectResourceLine(models.Model):
    _name = "project.resource.line"
    _description = "Project Resource Line"
    _rec_name = "display_name"

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        required=True,
        ondelete="cascade",
    )
    role_id = fields.Many2one(
        "planning.role",
        string="Role",
        required=False,
        help="Role associated with this resource line.",
    )

    role_cost = fields.Monetary(
        string="Hourly Cost",
        related="role_id.cost",
        currency_field="currency_id",
        store=True,
        help="Cost per hour for this role.",
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        help="Employee assigned to this resource line.",
    )

    price_per_hour = fields.Monetary(
        string="Unit Price",
        required=True,
        currency_field="currency_id",
        help="Hourly rate for this resource to be sold.",
    )
    quantity_hours = fields.Float(
        string="Quantity Hours",
        required=True,
        digits=(16, 2),
        help="Total number of hours estimated for this resource.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )
    subtotal_price = fields.Monetary(
        string="Subtotal Price",
        compute="_compute_subtotal_price",
        store=True,
        readonly=True,
        currency_field="currency_id",
    )

    # Subtotal (Price):  quantity_hours by price_per_hour
    @api.depends("quantity_hours", "price_per_hour")
    def _compute_subtotal_price(self):
        for line in self:
            line.subtotal_price = line.quantity_hours * line.price_per_hour

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for line in self:
            if line.employee_id and line.employee_id.default_planning_role_id:
                line.role_id = line.employee_id.default_planning_role_id
            else:
                line.role_id = False
