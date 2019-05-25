from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import random
import string

Base = declarative_base()

sysRand = random.SystemRandom()
secret_key = ''.join(sysRand.choice(string.ascii_uppercase + string.digits) for x in range(32))

class User(Base):
    """users"""
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    picture = Column(String)
    email = Column(String, index=True)
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
    	s = Serializer(secret_key, expires_in = expiration)
    	return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
    	s = Serializer(secret_key)
    	try:
    		data = s.loads(token)
    	except SignatureExpired:
    		#Valid Token, but expired
    		return None
    	except BadSignature:
    		#Invalid Token
    		return None
    	user_id = data['id']
    	return user_id
    
class Category(Base):
    """the catagory table contains categories, which will display items"""
    __tablename__ = 'Category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """returns category in a serializeable format"""
        return {
            'name': self.name,
            'id': self.id
        }

class Item(Base):
    """item table contains all items"""
    __tablename__ = 'Item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('Category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """returns item in a serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description
        }

if __name__ == '__main__':
    engine = create_engine('sqlite:///all_info.db')
    Base.metadata.create_all(engine)
