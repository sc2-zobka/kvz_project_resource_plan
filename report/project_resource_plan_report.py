# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import timedelta


class ProjectResourcePlanReport(models.Model):
    _name = "project.resource.plan.report"
    _description = "Project Resource Plan Analysis Report"
    _auto = False
    _order = "employee_id, project_id, task_id, date DESC"

    # Dimensions
    employee_id = fields.Many2one("hr.employee", string="Employee", readonly=True)
    project_id = fields.Many2one("project.project", string="Project", readonly=True)
    task_id = fields.Many2one("project.task", string="Task", readonly=True)
    name = fields.Char(string="Description", readonly=True)
    date = fields.Date(string="Date", readonly=True)

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
        Optimized view with indexes and limited default scope
        """
        tools.drop_view_if_exists(self.env.cr, "project_resource_plan_report")

        # Create indexes first
        self._create_indexes()

        # Get stage_id once
        stage_id = self._get_in_progress_stage_id()

        # Create materialized view for better performance
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW project_resource_plan_report AS (
                SELECT
                    aal.id,
                    aal.employee_id,
                    aal.project_id,
                    aal.task_id,
                    aal.name,
                    aal.date,
                    aal.company_id,
                    aal.currency_id,
                    aal.unit_amount AS hours,
                    -1 * aal.unit_amount * COALESCE(emp.hourly_cost, 0) AS timesheet_cost,
                    aal.unit_amount * COALESCE(prl.price_per_hour, 0) AS timesheet_revenue
                FROM
                    account_analytic_line aal
                    INNER JOIN hr_employee emp ON aal.employee_id = emp.id
                    INNER JOIN project_project pp ON aal.project_id = pp.id
                    LEFT JOIN LATERAL (
                        SELECT price_per_hour 
                        FROM project_resource_line prl
                        WHERE prl.project_id = pp.id 
                        AND prl.employee_id = emp.id
                        LIMIT 1
                    ) prl ON true
                WHERE
                    aal.project_id IS NOT NULL
                    AND pp.revenue_and_cost_report = TRUE
                    AND pp.stage_id = %(stage_id)s
                    -- IMPORTANT: Limit default scope to recent data
                    AND aal.date >= CURRENT_DATE - INTERVAL '3 months'
            );
        """,
            {"stage_id": stage_id},
        )

    def _get_in_progress_stage_id(self):
        """Get the 'In Progress' stage ID efficiently"""
        result = self.env["ir.model.data"]._xmlid_to_res_id(
            "project.project_project_stage_1", raise_if_not_found=False
        )
        return result or None

    def _create_indexes(self):
        """Create indexes for optimal performance"""
        indexes = [
            # Composite index for the main WHERE clause
            (
                "idx_aal_project_date_employee",
                "account_analytic_line",
                "(project_id, date DESC, employee_id) WHERE project_id IS NOT NULL",
            ),
            # Index for project filtering
            (
                "idx_pp_revenue_stage",
                "project_project",
                "(id) WHERE revenue_and_cost_report = TRUE",
            ),
            # Index for resource line lookup
            ("idx_prl_lookup", "project_resource_line", "(project_id, employee_id)"),
            # Index for employee cost lookup
            ("idx_emp_hourly_cost", "hr_employee", "(id, hourly_cost)"),
        ]

        for index_name, table_name, columns in indexes:
            self.env.cr.execute(f"""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = '{index_name}'
                    ) THEN
                        CREATE INDEX {index_name} ON {table_name} {columns};
                    END IF;
                END $$;
            """)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override to implement pagination and lazy loading"""

        # Force a reasonable limit if not specified
        if limit is None or limit > 1000:
            limit = 1000

        # Add date filter if not present
        if domain and not any(
            "date" in str(d[0]) for d in domain if isinstance(d, (list, tuple))
        ):
            # Default to last 3 months
            three_months_ago = fields.Date.today() - timedelta(days=90)
            domain = [("date", ">=", three_months_ago)] + (domain or [])

        return super().search_read(domain, fields, offset, limit, order)

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        """Implement efficient grouping with lazy loading"""

        # For initial load, force aggregation at higher levels
        if lazy and len(groupby) > 2:
            # If trying to group by more than 2 levels initially, limit it
            groupby = groupby[:2]

        # Add date filtering for performance
        if not any("date" in str(d[0]) for d in domain if isinstance(d, (list, tuple))):
            three_months_ago = fields.Date.today() - timedelta(days=90)
            domain = [("date", ">=", three_months_ago)] + domain

        # Limit the number of groups returned
        if limit is None and lazy:
            limit = 200  # Reasonable default for pivot views

        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
