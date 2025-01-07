# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        SQL = """
WITH refund_lines AS (
    SELECT
        aml.id AS refund_line_id,
        aml.move_id AS refund_id,
        aml.product_id,
        aml.name,
        am.reversed_entry_id AS invoice_id
    FROM
        account_move_line aml
    JOIN
        account_move am ON aml.move_id = am.id
    WHERE
        am.move_type IN ('out_refund', 'in_refund')
        AND am.reversed_entry_id IS NOT NULL
),
matched_lines AS (
    SELECT
        rl.refund_line_id,
        il.id AS invoice_line_id,
        ROW_NUMBER() OVER (
            PARTITION BY rl.refund_line_id
            ORDER BY
                CASE
                    WHEN rl.product_id = il.product_id THEN 1
                    WHEN rl.name = il.name THEN 2
                    ELSE 3
                END
        ) AS match_priority
    FROM
        refund_lines rl
    JOIN
        account_move_line il ON rl.invoice_id = il.move_id
    WHERE
        (rl.product_id IS NOT NULL AND rl.product_id = il.product_id)
        OR rl.name = il.name
)
UPDATE account_move_line aml
SET origin_line_id = ml.invoice_line_id
FROM matched_lines ml
WHERE
    aml.id = ml.refund_line_id
    AND ml.match_priority = 1;
"""
        env.cr.execute(SQL)
