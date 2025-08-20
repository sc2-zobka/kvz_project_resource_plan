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
        required=True,
        help="Role associated with this resource line.",
    )

    role_cost = fields.Monetary(
        string="Role Cost",
        related="role_id.cost",
        currency_field="currency_id",
        store=True,
    )

    price_per_hour = fields.Monetary(
        string="Price per Hour",
        required=True,
        currency_field="currency_id",
    )
    amount_of_hours = fields.Float(
        string="Amount of Hours",
        required=True,
        digits=(16, 2),
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )
    subtotal_bu = fields.Float(
        string="Subtotal BU",
        compute="_compute_subtotal_bu",
        readonly=True,
        store=True,
        digits=(16, 2),
    )

    subtotal_price = fields.Monetary(
        string="Subtotal Price",
        compute="_compute_subtotal_price",
        store=True,
        readonly=True,
        currency_field="currency_id",
    )

    # Subtotal (BU):  amount_of_hours by role_id.factor_bu
    @api.depends("amount_of_hours", "role_id.factor_bu")
    def _compute_subtotal_bu(self):
        for line in self:
            line.subtotal_bu = line.amount_of_hours * line.role_id.factor_bu

    # Subtotal (Price):  amount_of_hours by price_per_hour
    @api.depends("amount_of_hours", "price_per_hour")
    def _compute_subtotal_price(self):
        for line in self:
            line.subtotal_price = line.amount_of_hours * line.price_per_hour
