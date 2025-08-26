# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    resource_line_ids = fields.One2many(
        "project.resource.line",
        "project_id",
        string="Resource Lines",
    )
    total_resource_amount = fields.Monetary(
        string="Total Resource Amount",
        compute="_compute_total_resource_amount",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("resource_line_ids.subtotal_price")
    def _compute_total_resource_amount(self):
        for project in self:
            project.total_resource_amount = sum(
                project.resource_line_ids.mapped("subtotal_price")
            )
