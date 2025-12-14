from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class LinkedInPage(db.Model):
    __tablename__ = 'linkedin_pages'

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(500))
    url = db.Column(db.String(1000))
    profile_pic_url = db.Column(db.Text)
    description = db.Column(db.Text)
    website = db.Column(db.String(500))
    industry = db.Column(db.String(255))
    followers_count = db.Column(db.Integer, default=0)
    employees_count = db.Column(db.Integer, default=0)
    employees_text = db.Column(db.String(50))
    specialities = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    last_scraped = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship('Post', backref='page', lazy=True, cascade='all, delete-orphan')
    employees = db.relationship('Employee', backref='page', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_posts=False, include_employees=False):
        data = {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'profile_pic_url': self.profile_pic_url,
            'description': self.description,
            'website': self.website,
            'industry': self.industry,
            'followers_count': self.followers_count,
            'employees_count': self.employees_count,
            'employees_text': self.employees_text or str(self.employees_count) if self.employees_count else '0',
            'specialities': self.specialities,
            'ai_summary': self.ai_summary,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        # ALWAYS include posts and employees arrays (even if empty)
        if include_posts:
            data['posts'] = [post.to_dict() for post in self.posts]
        else:
            data['posts'] = []

        if include_employees:
            data['employees'] = [emp.to_dict() for emp in self.employees]
        else:
            data['employees'] = []

        return data


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.String(255), primary_key=True)
    page_id = db.Column(db.String(255), db.ForeignKey('linkedin_pages.id'), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.Text)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    posted_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'page_id': self.page_id,
            'content': self.content,
            'image_url': self.image_url,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.String(255), primary_key=True)
    post_id = db.Column(db.String(255), db.ForeignKey('posts.id'), nullable=False)
    author = db.Column(db.String(500))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'author': self.author,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.String(255), primary_key=True)
    page_id = db.Column(db.String(255), db.ForeignKey('linkedin_pages.id'), nullable=False)
    name = db.Column(db.String(500))
    headline = db.Column(db.String(1000))
    profile_url = db.Column(db.String(1000))
    profile_pic_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'page_id': self.page_id,
            'name': self.name,
            'headline': self.headline,
            'profile_url': self.profile_url,
            'profile_pic_url': self.profile_pic_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
