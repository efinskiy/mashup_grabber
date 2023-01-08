from ext import db
from models import User, Channels, Track

session = db.Session()
db.drop_all()
db.create_all()
