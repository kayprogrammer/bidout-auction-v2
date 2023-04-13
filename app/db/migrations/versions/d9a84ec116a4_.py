"""empty message

Revision ID: d9a84ec116a4
Revises: 5b9ee3b1fde0
Create Date: 2023-04-13 00:42:03.508603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d9a84ec116a4"
down_revision = "5b9ee3b1fde0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("listings", sa.Column("bids_count", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("listings", "bids_count")
    # ### end Alembic commands ###
