"""add training_video table"""

from alembic import op
import sqlalchemy as sa

# use a new id here – just make it unique
revision = "abcd1234addtraining"
down_revision = "6503d6a69bf9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "training_video",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True, server_default="General"),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("customer.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )


def downgrade():
    op.drop_table("training_video")

