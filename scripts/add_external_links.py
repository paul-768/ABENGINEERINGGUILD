import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Topic, StudyMaterial

app = create_app()

with app.app_context():
    # Update topics with external links
    topics = Topic.query.all()
    external_links = {
        "Farm Machinery": "https://drive.google.com/drive/folders/1SzZ5PepJt3tPdBnawytHtz8qiobVqQqO?usp=sharing",
        "Soil & Water Management": "https://drive.google.com/drive/folders/11vm_HYE-vzPVg5GiVN__yasjsggZcxl0?usp=sharing",
        "Post-Harvest Technology": "https://drive.google.com/drive/folders/17-eHOvmhu6sMmH6kcNvc3E5xwq_37-31?usp=sharing",
        "Environmental Engineering": "https://drive.google.com/drive/folders/17-eHOvmhu6sMmH6kcNvc3E5xwq_37-31?usp=sharing",
        "PAES Standards": "https://amtec.uplb.edu.ph/"
    }
    
    for topic in topics:
        if topic.name in external_links:
            topic.external_link = external_links[topic.name]
    
    # Update study materials with external links
    materials = StudyMaterial.query.all()
    material_links = {
        "Introduction to Post-Harvest Technology": "https://drive.google.com/drive/folders/17-eHOvmhu6sMmH6kcNvc3E5xwq_37-31?usp=sharing",
    }
    
    for material in materials:
        if material.title in material_links:
            material.external_link = material_links[material.title]
    
    db.session.commit()
    print("External links added to database")