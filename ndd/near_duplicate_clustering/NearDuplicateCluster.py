from sqlalchemy import Column, Integer, String
from GalleryImage import Base

class NearDuplicateCluster(Base):
    __tablename__ = "nearDuplicateCluster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    size = Column(Integer, nullable=False)
    main_image_id = Column(Integer, nullable=False)
    similar_image_ids = Column(String, nullable=False)

    def __init__(self, size, main_image_id, similar_image_ids):
        self.size = size
        self.main_image_id = main_image_id
        self.similar_image_ids = similar_image_ids