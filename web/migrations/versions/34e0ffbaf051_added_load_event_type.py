"""Added 'load' event type

Revision ID: 34e0ffbaf051
Revises: 6903aa47f36d
Create Date: 2022-01-17 21:25:27.621965

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34e0ffbaf051'
down_revision = 'cd110b1bb3ef'
branch_labels = None
depends_on = None

# https://stackoverflow.com/questions/14845203/altering-an-enum-field-using-alembic
old_enum = sa.Enum('focus', 'click', 'submit')
new_enum = sa.Enum('focus', 'click', 'submit', 'load')
new_enum_val = 'load'

column_name = 'event'
default_enum_val = 'focus'
table = sa.table('interaction', sa.Column(column_name, new_enum, nullable=False))

def upgrade():
    with op.batch_alter_table('interaction', schema=None) as batch_op:
        batch_op.alter_column(
            'event',
            existing_type=old_enum,
            type_=new_enum,
            existing_nullable=False
        )


def downgrade():
    with op.batch_alter_table('interaction', schema=None) as batch_op:
        default = {}
        default[column_name] = default_enum_val
        batch_op.execute(table.update().where(table.c[column_name]==new_enum_val)
               .values(**default))
        batch_op.alter_column(
            'event',
            existing_type=new_enum,
            type_=old_enum,
            existing_nullable=False
        )
