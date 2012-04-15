from ireul.environment import metadata

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary,
)
from ireul.lib.fields import EncodingParams

blob = \
        Table('blob', metadata,
              Column('id', Integer, primary_key=True),
              Column('cont_addr', String, nullable=False, unique=True),
              Column('mime_type', String, nullable=False),
              Column('added_at', DateTime, nullable=False))

track_orig = \
        Table('track_orig', metadata,
              Column('id', Integer, primary_key=True),
              Column('blob_id', Integer,
                     ForeignKey(blob.c.id),
                     nullable=False,
                     unique=True),
              # pickle the metadata for later
              Column('metadata', LargeBinary),
              Column('artist', String),
              Column('title', String),
             )

track_derived = \
        Table('track_derived', metadata,
              Column('id', Integer, primary_key=True),
              Column('track_orig_id', Integer,
                     ForeignKey(track_orig.c.id),
                     nullable=False
                    ),
              Column('blob_id', Integer,
                     ForeignKey(blob.c.id),
                     nullable=False,
                     unique=True),
              Column('codec', String, nullable=True),
              Column('encoding_params', EncodingParams, nullable=True),
              Column('added_at', DateTime))

user = \
        Table('user', metadata,
                Column('id', Integer, primary_key=True),
                Column('username', String, nullable=False, unique=True))

fave = \
        Table('fave', metadata,
                Column('id', Integer, primary_key=True),
                Column('track_orig_id', Integer,
                    ForeignKey(track_orig.c.id),
                    nullable=False),
                Column('user_id', Integer,
                    ForeignKey(user.c.id),
                    nullable=False))

