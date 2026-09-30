"""make stored query hashes unique

Revision ID: 3b7a8c1d5e90
Revises: 99e5b6ace0a1
"""
from alembic import op
import sqlalchemy as sa


revision = '3b7a8c1d5e90'
down_revision = '99e5b6ace0a1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'sparql_query_hash' not in inspector.get_table_names():
        return

    unique_constraints = inspector.get_unique_constraints('sparql_query_hash')
    hash_is_unique = any(
        constraint.get('column_names') == ['query_hash_format']
        for constraint in unique_constraints
    )
    if not hash_is_unique:
        op.execute(sa.text("""
            DELETE FROM sparql_query_hash AS duplicate
            USING sparql_query_hash AS original
            WHERE duplicate.query_hash_format = original.query_hash_format
              AND duplicate.id > original.id
        """))
        op.create_unique_constraint(
            'uq_sparql_query_hash_format',
            'sparql_query_hash',
            ['query_hash_format'],
        )


def downgrade():
    inspector = sa.inspect(op.get_bind())
    unique_names = {
        constraint['name']
        for constraint in inspector.get_unique_constraints('sparql_query_hash')
    }
    if 'uq_sparql_query_hash_format' in unique_names:
        op.drop_constraint(
            'uq_sparql_query_hash_format',
            'sparql_query_hash',
            type_='unique',
        )
