from sqlalchemy import Integer, Column, String, Boolean
from ext import db


class User(db.Model):
    id = Column(Integer, primary_key=True)
    uid = Column(Integer)
    is_admin = Column(Boolean, default=False)


class Channels(db.Model):
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    enabled = Column(Boolean, default=False)
    title = Column(String())
    upload_to_custom = Column(Boolean, default=False)


class Track(db.Model):
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    track_message_id = Column(Integer)
    uploaded = Column(Boolean, default=False)
