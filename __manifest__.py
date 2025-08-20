# -*- coding: utf-8 -*-
{
    "name": "Project Resource Plan",
    "summary": "Resource planning for projects",
    "version": "17.0.0.0.1",
    "author": "Kuvasz Solutions S.A.",
    "website": "https://www.kvz.cl",
    "category": "Human Resources",
    "license": "LGPL-3",
    "depends": ["planning", "project", "resource"],
    "data": [
        "security/ir.model.access.csv",
        "views/planning_role_view.xml",
        "views/employee_menu.xml",
        "views/project_project_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
