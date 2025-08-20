# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    resource_line_ids = fields.One2many(
        "project.resource.line",
        "project_id",
        string="Resource Lines",
    )
