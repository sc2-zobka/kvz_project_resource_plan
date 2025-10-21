# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _


class ProjectResourcePlanReport(models.Model):
    _name = 'project.resource.plan.report'
    _description = 'Project Resource Plan Analysis Report'
    _auto = False  
    _order = 'employee_id, project_id'

    # Dimensions
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    role_id = fields.Many2one('planning.role', string='Role', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    
    # Measures
    hours = fields.Float(string='Hours', readonly=True, digits=(16, 2))
    price_per_hour = fields.Monetary(string='Precio Hora', readonly=True, 
                                    currency_field='currency_id')
    cost_per_hour = fields.Monetary(string='Costo Hora', readonly=True,
                                   currency_field='currency_id')
    total_price = fields.Monetary(string='Total Precio', readonly=True,
                                 currency_field='currency_id')
    total_cost = fields.Monetary(string='Total Costo', readonly=True,
                                currency_field='currency_id')
    
    # Utility fields
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    
    # Additional useful dimensions
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    month = fields.Char(string='Month', readonly=True)
    year = fields.Char(string='Year', readonly=True)

    def init(self):
        """
        Creates or replaces the SQL view for Project Resource Plan Report.
        This view aggregates timesheet data with pricing and cost information.
        """
        tools.drop_view_if_exists(self.env.cr, 'project_resource_plan_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW project_resource_plan_report AS (
                SELECT
                    row_number() OVER() AS id,
                    aal.employee_id,
                    aal.project_id,
                    emp.department_id,
                    prl.role_id,
                    aal.date,
                    TO_CHAR(aal.date, 'YYYY-MM') AS month,
                    TO_CHAR(aal.date, 'YYYY') AS year,
                    aal.company_id,
                    aal.currency_id,
                    SUM(aal.unit_amount) AS hours,
                    -- Get price per hour from resource line or use a default
                    COALESCE(prl.price_per_hour, 0) AS price_per_hour,
                    -- Get cost per hour from employee or from role
                    COALESCE(emp.hourly_cost, pr.cost, 0) AS cost_per_hour,
                    -- Calculate totals
                    SUM(aal.unit_amount) * COALESCE(prl.price_per_hour, 0) AS total_price,
                    SUM(aal.unit_amount) * COALESCE(emp.hourly_cost, pr.cost, 0) AS total_cost
                FROM
                    account_analytic_line aal
                    INNER JOIN hr_employee emp ON aal.employee_id = emp.id
                    INNER JOIN project_project pp ON aal.project_id = pp.id
                    LEFT JOIN project_resource_line prl 
                        ON prl.project_id = pp.id 
                        AND prl.employee_id = emp.id
                    LEFT JOIN planning_role pr ON prl.role_id = pr.id
                WHERE
                    aal.project_id IS NOT NULL
                GROUP BY
                    aal.employee_id,
                    aal.project_id,
                    emp.department_id,
                    prl.role_id,
                    aal.date,
                    aal.company_id,
                    aal.currency_id,
                    prl.price_per_hour,
                    emp.hourly_cost,
                    pr.cost
            );
        """)