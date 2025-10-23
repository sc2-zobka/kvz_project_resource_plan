# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _


class ProjectResourcePlanReport(models.Model):
    _name = "project.resource.plan.report"
    _description = "Project Resource Plan Analysis Report"
    _auto = False
    _order = "employee_id, project_id, task_id"

    # Dimensions
    employee_id = fields.Many2one("hr.employee", string="Employee", readonly=True)
    project_id = fields.Many2one("project.project", string="Project", readonly=True)
    task_id = fields.Many2one("project.task", string="Task", readonly=True)
    name = fields.Char(string="Description", readonly=True)
    date = fields.Date(string="Date", readonly=True)
    month = fields.Char(string="Month", readonly=True)
    year = fields.Char(string="Year", readonly=True)

    # Measures
    hours = fields.Float(string="Hours", readonly=True, digits=(16, 2))
    timesheet_cost = fields.Float(string="Timesheet Cost", readonly=True)
    timesheet_revenue = fields.Monetary(
        string="Timesheet Revenue", readonly=True, currency_field="currency_id"
    )

    # Utility fields
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)

    def init(self):
        """
        Creates or replaces the SQL view for Project Resource Plan Report.
        This view aggregates timesheet data with pricing and cost information.
        """
        tools.drop_view_if_exists(self.env.cr, "project_resource_plan_report")
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW project_resource_plan_report AS (
                SELECT
                    row_number() OVER() AS id,
                    aal.employee_id,
                    aal.project_id,
                    aal.task_id,
                    aal.name,
                    aal.date,
                    TO_CHAR(aal.date, 'YYYY-MM') AS month,
                    TO_CHAR(aal.date, 'YYYY') AS year,
                    aal.company_id,
                    aal.currency_id,
                    SUM(aal.unit_amount) AS hours,
                    -1 * SUM(aal.unit_amount * COALESCE(emp.hourly_cost, 0)) AS timesheet_cost,
                    SUM(aal.unit_amount * COALESCE(prl.price_per_hour, 0)) AS timesheet_revenue                    
                FROM
                    account_analytic_line aal
                    INNER JOIN hr_employee emp ON aal.employee_id = emp.id
                    INNER JOIN project_project pp ON aal.project_id = pp.id
                    LEFT JOIN project_resource_line prl 
                        ON prl.project_id = pp.id 
                        AND prl.employee_id = emp.id
                WHERE
                    aal.project_id IS NOT NULL
                    AND pp.revenue_and_cost_report = TRUE
                    AND pp.stage_id = (
                        SELECT res_id 
                        FROM ir_model_data 
                        WHERE module = 'project' 
                        AND name = 'project_project_stage_1'
                        AND model = 'project.project.stage'
                        LIMIT 1
                    )
                GROUP BY
                    aal.employee_id,
                    aal.project_id,
                    aal.task_id,
                    aal.name,
                    aal.date,
                    aal.company_id,
                    aal.currency_id
            );
        """)
