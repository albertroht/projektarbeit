from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GalleryImage(Base):

    __tablename__ = "galleryimage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(250), nullable=False, unique=True)
    timestamp = Column(Integer, nullable=False)

    def __init__(self, filename, timestamp):
        self.filename = filename
        self.timestamp = timestamp
        self.image_vector = None

    def getData(self):
        return {"filename" : self.filename, "timestamp" : self.timestamp}