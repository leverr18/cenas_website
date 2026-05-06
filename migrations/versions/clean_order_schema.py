"""Clean order schema: Order batch + OrderItem, drop customer.location"""

from alembic import op
import sqlalchemy as sa

revision = "clean_order_schema_001"
down_revision = "abcd1234addtraining"
branch_labels = None
depends_on = None


def upgrade():
    # Drop old per-item order table
    op.drop_table('order')

    # New Order table — one row per cart submission
    op.create_table(
        'order',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=100), nullable=False, server_default='Submitted'),
        sa.Column('customer_link', sa.Integer(), sa.ForeignKey('customer.id'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # OrderItem table — one line per order
    op.create_table(
        'order_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_link', sa.Integer(), sa.ForeignKey('order.id'), nullable=False),
        sa.Column('product_name', sa.String(length=100), nullable=False),
        sa.Column('product_category', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Drop unused customer.location if it still exists
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='customer' AND column_name='location'"
    ))
    if result.fetchone():
        with op.batch_alter_table('customer') as batch_op:
            batch_op.drop_column('location')


def downgrade():
    with op.batch_alter_table('customer') as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(length=100), nullable=True))

    op.drop_table('order_item')
    op.drop_table('order')

    op.create_table(
        'order',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=100), nullable=False),
        sa.Column('ordered_at', sa.DateTime(), nullable=True),
        sa.Column('customer_link', sa.Integer(), sa.ForeignKey('customer.id'), nullable=False),
        sa.Column('product_link', sa.Integer(), sa.ForeignKey('product.id'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )