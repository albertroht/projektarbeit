from sqlalchemy import Column, Integer, String
from GalleryImage import Base

class TemporalCluster(Base):
    __tablename__ = "temporalcluster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_ids = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    median_timestamp = Column(Integer, nullable=False, unique=True)

    def __init__(self, image_ids, size, median_timestamp):
        self.image_ids = image_ids
        self.size = size
        self.median_timestamp = median_timestamp

    def getData(self):
        return {"image_ids": self.image_ids, "size": self.size, "median_timestamp": self.median_timestamp}