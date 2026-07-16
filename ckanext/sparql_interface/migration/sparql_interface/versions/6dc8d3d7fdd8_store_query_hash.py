"""store query hash

Revision ID: 6dc8d3d7fdd8
Revises: 
Create Date: 2024-08-30 10:54:27.671276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dc8d3d7fdd8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('sparql_query_hash'):
        return

    op.create_table('sparql_query_hash',
                    sa.Column('id', sa.Integer, primary_key=True, nullable=False),
                    sa.Column('timestamp', sa.TIMESTAMP(), nullable=False),
                    sa.Column('query_long_format', sa.String, nullable=False),
                    sa.Column('query_hash_format', sa.String, nullable=False),
                    )

def downgrade():
    pass
