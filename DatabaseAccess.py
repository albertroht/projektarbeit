from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DropTable

Base = declarative_base()

class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True, autoincrement=True)
    selected = Column(Boolean)
    aesthetic_score = Column(Float)
    faces_count = Column(Integer)
    
    def __init__(self):
        self.selected = False
        
class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, nullable=False)
    tag_name = Column(String, nullable=False)
    score = Column(Float)

    def __init__(self, image_id, tag_name, score):
        self.image_id = image_id
        self.tag_name = tag_name
        self.score = score
        
class NearDuplicateCluster(Base):
    __tablename__ = "nearDuplicateCluster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_ids = Column(String, nullable=False)

    def __init__(self, image_ids):
        self.image_ids = image_ids
        
class DatabaseAccess:
    def __init__(self, database_name):
        db_engine = create_engine("sqlite:///{}.db".format(database_name),connect_args={'check_same_thread': False})
        Base.metadata.bind = db_engine
        Base.metadata.create_all(db_engine)
        DBSession = sessionmaker(bind=db_engine)
        self.session = DBSession()
        
    def save_object(self, object):
        self.session.add(object)
        try:
            self.session.commit()
        except:
            self.session.rollback()
            print("can't add object")
            
    def get_image_objects(self):
        return [i for i in self.session.query(Image)]
    
    def get_image(self, image_id):
        return self.session.query(Image).filter_by(id = image_id).first()
    
    def delete_image(self, image_id):
        for ndc in self.session.query(NearDuplicateCluster):
            if str(image_id) in ndc.image_ids.split("/"):
                self.session.query(NearDuplicateCluster).filter_by(id=ndc.id).delete()
        self.session.query(Image).filter_by(id=int(image_id)).delete()
        self.session.commit()
        return
    
    def updateImageSelected(self, image_id, selected):
        self.session.query(Image).filter_by(id = image_id).update({"selected" : selected})
        
    def updateImageAesthetic(self, image_id, aesthetic_score):
        self.session.query(Image).filter_by(id = image_id).update({"aesthetic_score" : aesthetic_score})
        self.session.commit()
        
    def updateFacesCount(self, image_id, faces_count):
        self.session.query(Image).filter_by(id = image_id).update({"faces_count" : faces_count})
        self.session.commit()
        
    
    def getTags(self, image_id):
        tags = self.session.query(Tag).filter_by(image_id = image_id)
        return [(tag.tag_name,round(tag.score,2)) for tag in tags]
    
    def getSelected(self, image_id):
        image = self.session.query(Image).filter_by(id = int(image_id)).first()
        print(image)
        return image.selected
    
    def getImagesWithTag(self, tag_name):
        tags = self.session.query(Tag).filter_by(tag_name = tag_name)
        image_ids = list(set([tag.image_id for tag in tags]))
        images = [self.get_image(image_id) for image_id in image_ids]
        return images
        
    def getTagOccurences(self):
        tags = self.session.query(Tag)
        tag_names = [tag.tag_name for tag in tags]
        tag_names_unique = list(set(tag_names))
        
        tag_occurence_list = [(tag_name,tag_names.count(tag_name)) for tag_name in tag_names_unique]
        tag_occurence_list.sort(key=lambda tup: tup[1], reverse=True)
        return tag_occurence_list
        
    def dropNearDuplicateClusterTable(self):
        self.session.query(NearDuplicateCluster).delete()
        
    def getAllCluster(self):
        return self.session.query(NearDuplicateCluster)