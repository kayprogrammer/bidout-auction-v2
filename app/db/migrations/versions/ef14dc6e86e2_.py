"""empty message

Revision ID: ef14dc6e86e2
Revises: 9118a154eee6
Create Date: 2023-04-27 22:49:15.734991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ef14dc6e86e2"
down_revision = "9118a154eee6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "suscribers", ["email"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "suscribers", type_="unique")
    # ### end Alembic commands ###