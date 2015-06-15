"""alter users date fields with time zone

Revision ID: d3e7ccd03d3
Revises: 
Create Date: 2015-06-16 02:13:17.454831

"""

# revision identifiers, used by Alembic.
revision = 'd3e7ccd03d3'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('users', 'last_login_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))
    op.alter_column('users', 'registered_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))

def downgrade():
    pass
