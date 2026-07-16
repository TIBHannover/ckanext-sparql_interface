"""change spaqrl hash timezone

Revision ID: 99e5b6ace0a1
Revises: 6dc8d3d7fdd8
Create Date: 2024-09-24 16:51:16.542489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99e5b6ace0a1'
down_revision = '6dc8d3d7fdd8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('sparql_query_hash'):
        return

    columns = {
        column['name']: column
        for column in inspector.get_columns('sparql_query_hash')
    }
    timestamp = columns.get('timestamp')
    if timestamp is None or isinstance(timestamp['type'], sa.TIMESTAMP):
        return

    op.alter_column('sparql_query_hash', 'timestamp',
                    existing_type=timestamp['type'],
                    type_=sa.TIMESTAMP(),
                    nullable=False,
                    postgresql_using="timestamp::timestamp")

def downgrade():
    pass
