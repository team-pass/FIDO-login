"""Remove non-NULL constrants for users

Revision ID: cd110b1bb3ef
Revises: 6903aa47f36d
Create Date: 2022-01-21 11:32:28.496016

"""
from uuid import uuid4
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd110b1bb3ef'
down_revision = '6903aa47f36d'
branch_labels = None
depends_on = None

import logging
logger = logging.getLogger(__name__)


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('email', nullable=True, existing_type=sa.String(80))
        batch_op.alter_column('display_name', nullable=True, existing_type=sa.String(80))

    logger.info("Finished upgrade :)")


def downgrade():
    users =  sa.table('user', sa.Column('id', sa.Integer), sa.Column('email', sa.String), sa.Column('display_name', sa.String))
    
    # Generate unique null emails
    op.execute(users.update()
        .where(users.c.email==None)
        .values(email=sa.cast(users.c.id, sa.String) + "@fake-email.com")
    )
    op.execute(users.update()
        .where(users.c.display_name==None)
        .values(display_name='Nonexistent User')
    )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('email', nullable=False, existing_type=sa.String(80))
        batch_op.alter_column('display_name', nullable=False, existing_type=sa.String(80))
