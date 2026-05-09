import os
from flask import current_app

def get_paes_file_path(code):
    """Generate file path for PAES standards"""
    filename = f"{code.lower().replace(' ', '_')}.pdf"
    return os.path.join(current_app.static_folder, 'paes', filename)

def get_material_file_path(material_id, filename):
    """Generate file path for study materials"""
    return os.path.join(current_app.static_folder, 'materials', f"{material_id}_{filename}")

def search_materials(keyword):
    """Search function for materials across all categories"""
    from app.models import Topic, StudyMaterial, PAESStandard
    
    results = {
        'topics': [],
        'materials': [],
        'paes_standards': []
    }
    
    if not keyword:
        return results
    
    # Search in topics
    results['topics'] = Topic.query.filter(
        (Topic.name.ilike(f'%{keyword}%')) | 
        (Topic.description.ilike(f'%{keyword}%'))
    ).all()
    
    # Search in study materials
    results['materials'] = StudyMaterial.query.filter(
        (StudyMaterial.title.ilike(f'%{keyword}%')) | 
        (StudyMaterial.content.ilike(f'%{keyword}%'))
    ).all()
    
    # Search in PAES standards
    results['paes_standards'] = PAESStandard.query.filter(
        (PAESStandard.code.ilike(f'%{keyword}%')) | 
        (PAESStandard.title.ilike(f'%{keyword}%')) | 
        (PAESStandard.description.ilike(f'%{keyword}%'))
    ).all()
    
    return results