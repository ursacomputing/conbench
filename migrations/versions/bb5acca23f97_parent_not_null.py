"""parent not null

Revision ID: bb5acca23f97
Revises: 662175f2e6c6
Create Date: 2021-04-21 11:11:00.621174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bb5acca23f97"
down_revision = "662175f2e6c6"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "commit", "parent", existing_type=sa.VARCHAR(length=50), nullable=False
    )


def downgrade():
    op.alter_column(
        "commit", "parent", existing_type=sa.VARCHAR(length=50), nullable=True
    )
