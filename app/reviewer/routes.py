from flask import render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.models import Topic, StudyMaterial, PAESStandard, MaterialLink
from app.reviewer import reviewer_bp
from sqlalchemy import text
from app import db
import os

# Define topic display names and internal file structure
TOPIC_CONFIG = {
    "AREA I": {
        "display_name": "AREA I",
        "description": "Agricultural and Biosystems Engineering - Power, Mechanization, and Management",
        "folder": "area_i",
        "materials": [
            {
                "title": "1. Agricultural and Biosystems Power Engineering",
                "file": "agricultural_biosystems_power_engineering.pdf", 
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1DQGPJz2LPzJBgRQ_2QjO9ftGcA7hnkoe?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8z3Uf6yYJjM8EQTiCoQaSq"}
                ]
            },
            {
                "title": "2. Agricultural and Biosystems Mechanization Planning, Operation, Maintenance, Management and Manufacturing",
                "file": "agricultural_biosystems_mechanization.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1PJDwDxgyQFrw2Mwyv-o5ssnedIMZnPGM?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9oAB5sMK-xH1gHS-qtHlbG"}
                ]
            },
            {
                "title": "3. Agricultural and Biosystems Machinery Specifications, Testing and Evaluation",
                "file": "machinery_specifications_testing.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1GgdpQS8PlrxkHgI0ZFjRg9qKEsyBjefA?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9GBGg--CcCFdwe33NuRWLl"}
                ]
            },
            {
                "title": "4. Agricultural and Biosystems Automation, Instrumentation and Control System",
                "file": "automation_instrumentation_control.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/14hUYndyELLqYWJK_Erox65ApWtdfUNJM?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-LuK6LhKvCktkq5wAOLfsO"}
                ]
            },
            {
                "title": "5. Project Management, Feasibility Study Preparation/Evaluation, Agricultural and Biosystems Research, Development and Extension",
                "file": "project_management_feasibility_research.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1syFqCnQI3fhnyX27pSXnLZr6x3pgy6Ca?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_J2RsZT80mLtYSdf5XJA0V"}
                ]
            },
            {
                "title": "6. Laws, Professional Standards and Ethics",
                "file": "laws_professional_standards_ethics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1A93sOwujkaU-ZxujnZ_RpHfkzOEsEXFL?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9NP7bCM_aVfTXRUOVH_ip9"}
                ]
            }
        ]
    },
    "AREA II": {
        "display_name": "AREA II", 
        "description": "Soil and Water Resources Engineering, Hydrology, and Environmental Sciences",
        "folder": "area_ii",
        "materials": [
            {
                "title": "1. Hydrology",
                "file": "hydrology.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1vKroKZf8m_Ho6p_3wzG4gYrU9DJahdW-?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_fOgAWLrmdXeRncqc_wn2O"}
                ]
            },
            {
                "title": "2. Irrigation and Drainage Engineering",
                "file": "irrigation_drainage_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1hVLoXzqOA11k-8jLw0BJUwNcbeIW_VRB?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_HIC0_WKgjHJq8Zfmi5VJt"}
                ]
            },
            {
                "title": "3. Soil and Water Resources Engineering",
                "file": "soil_water_resources_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1eIjK92LQr5i-y8DNQZ9wiEtYr_CUqEQ5?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_2luda2FU6olpm9imqTskn"}
                ]
            },
            {
                "title": "4. Aquaculture Engineering",
                "file": "aquaculture_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1if90Cuz6ngoTYdk3Pkn1uTkiGYGOTq0y?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9lUoiB5uX-kCpz3b_hWa_V"}
                ]
            },
            {
                "title": "5. Fundamentals of Agricultural, Fishery, Ecological and Environmental Sciences",
                "file": "agricultural_fishery_ecological_sciences.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1mbvp0V6dEnOGKyEPjRkzt80jephxTKpG?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-9OvdsxRPuKOrtGvbdQGo0"}
                ]
            },
            {
                "title": "6. Mathematics and Basic Engineering",
                "file": "mathematics_basic_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1DQttgUmNht0Q0438HTGKRpXKo5b6PEbW?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8BuKhfGiS-79f1s9nv-DYR"}
                ]
            }
        ]
    },
    "AREA III": {
        "display_name": "AREA III",
        "description": "Post-Harvest, Food Engineering, and Agricultural Structures", 
        "folder": "area_iii",
        "materials": [
            {
                "title": "1. Agricultural Buildings and Structures",
                "file": "agricultural_buildings_structures.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1QK6KyaNoFwWPgznWs8HG3U1KDRkH1QFG?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-pnksTUERO_emX6sE1YdBp"}
                ]
            },
            {
                "title": "2. Farm Electrification",
                "file": "farm_electrification.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1SBMnChCSlpErcDb4b1FlWP86lEyT1Xev?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_KVWRk-jWQPcbv_1QYJD9T"}
                ]
            },
            {
                "title": "3. Environment Engineering",
                "file": "environment_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1B7mTzvT0dnFfnegWnFnIrKYBLyHybcrw?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9k6JyNbzsgpJSRPLJG4J9y"}
                ]
            },
            {
                "title": "4. Agricultural and Bioprocess Engineering",
                "file": "agricultural_bioprocess_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1XnTvFfv7IIGJdoLnWO2q2FpX4bt_IOO7?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-kCNIw744PQPjKGe0fBYAp"}
                ]
            },
            {
                "title": "5. Food Engineering",
                "file": "food_engineering.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1GtV8_MryxcpfXxyXnpSVwF0LqbBMSpCW?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk--FAN0HT4FlK-VjsTMaH-E"}
                ]
            }
        ]
    },
    "Engineering Mathematics": {
        "display_name": "Engineering Mathematics",
        "description": "Comprehensive Mathematical Foundations for Agricultural and Biosystems Engineering",
        "folder": "engineering_math",
        "materials": [
            {
                "title": "1. Mathematics in the Modern World",
                "file": "mathematics_modern_world.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/19vVZOABCIYBnc63XLILKWYkZcExdSWG4?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_gftPwANFs09kIpraANt_g"}
                ]
            },
            {
                "title": "2. College Algebra",
                "file": "college_algebra.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1QCIiMwY5oOt1I8qaM6BUzz-fjnWEZD5A?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-KPWLHGGrWn44m8M440amh"}
                ]
            },
            {
                "title": "3. Plane and Solid Geometry",
                "file": "plane_solid_geometry.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1iZDVyHL92xpWnOWDERKUSZwqmWzUuhBl?usp=drive_links"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-DgLcYOvbfBg36EoEXwwmT"}
                ]
            },
            {
                "title": "4. Trigonometry",
                "file": "trigonometry.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1OW_0XGDrsnZlOcNqGhSFBJby7e461h7w?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8hcbJiti07Lw72-AbF6SIk"}
                ]
            },
            {
                "title": "5. Analytic Geometry",
                "file": "analytic_geometry.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1ktSFc3ciDQo2lYry8N7tP8-3bAhEQeQS?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8giGSQ3s4sCJ5NuiqO56hu"}
                ]
            },
            {
                "title": "6. Differential Calculus",
                "file": "differential_calculus.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1U15Ke-swyA15T_w4gK6fDkr-UjiVzcH5?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9ALojwyGhxV8Jci0tTsMSW"}
                ]
            },
            {
                "title": "7. Integral Calculus",
                "file": "integral_calculus.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/14uQSPRxsOKZPz0SGyClJnEU-0eFiczZv?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8JeQOXSe74DeZZnFHfc22G"}
                ]
            },
            {
                "title": "8. Differential Equations",
                "file": "differential_equations.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1RBVbpUJeHisiycuN36tVNBm6vm3QYvVH?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-nk_LIRCeV6zSwCqqdPxAZ"}
                ]
            },
            {
                "title": "9. Engineering Data Analysis (Probability and Statistics)",
                "file": "engineering_data_analysis.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1Sx4YZzCJZiBDCtTau3vWVVx1lvuGEbfZ?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8yP3KURcs1TK00RJlj0OoU"}
                ]
            },
            {
                "title": "10. Advanced Engineering Mathematics",
                "file": "advanced_engineering_mathematics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1B6sbmwQHagpHKk7QvT2a57gUzVkstxZq?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk9rEaoJBU_2UKl7mQbrb4lS"},
                ]
            },
            {
                "title": "11. Numerical Methods",
                "file": "numerical_methods.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1IRULF7BqcvxIByhBgLUs-USNCpYQ3_SN?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8rPZVRKlOoGGcGIV8v_uda"}
                ]
            },
            {
                "title": "12. Engineering Economics",
                "file": "engineering_economics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/16IOIm08dwr9ti7TixI70Isjk9Z6B45Q9?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_xmfQ-5V0jYe2v2TGMsKrC"}
                ]
            },
            {
                "title": "13. Fluid Mechanics Mathematics",
                "file": "fluid_mechanics_mathematics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1RSFhGyOvuKeLmrDvUIoJ5pUn8XVUABXU?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_MN8Ekv5DcVzvMvlSK3iy5"}
                ]
            },
            {
                "title": "14. Hydraulics and Hydrology Mathematics",
                "file": "hydraulics_hydrology_mathematics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1vpMXjUOmBElbIvtQxsZ8iduXd2XOqUeD?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk88VfMT-DEkL4SZJdSU-_I6"}
                ]
            },
            {
                "title": "15. Thermodynamics and Heat Transfer Mathematics",
                "file": "thermodynamics_heat_transfer.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1HXLiFrRPQEFXvTYIWPxNOVGXUBBvzmmX?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_evoh0kPe2FL24p-1_4Es5"}
                ]
            },
            {
                "title": "16. Engineering Mechanics Mathematics",
                "file": "engineering_mechanics_mathematics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1G4FgNwJ2nYulKrvaYtIpT8lhgsP1trFc?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8DLZsbWugNxalVmkzAN7I0"}
                ]
            },
            {
                "title": "17. Soil and Water Engineering Mathematics",
                "file": "soil_water_engineering_mathematics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/1q9WVvFRjxoCYw3qmIum_APyLFbNjEt6d?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk8LyrXghj9nUaYOBAbk6ArO"}
                ]
            },
            {
                "title": "18. Design Project / Thesis Mathematics",
                "file": "design_project_thesis_mathematics.pdf",
                "type": "pdf",
                "external_links": [
                    {"name": "Review Materials", "url": "https://drive.google.com/drive/folders/15eTGiZIBwehJ_vUUfR7QRxv3IUeMyry6?usp=drive_link"},
                    {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk__1B9XGy4_V6m10zfNYqf_"}
                ]
            }
        ]
    
    },
    "PAES Standards": {
    "display_name": "PAES Standards",
    "description": "Philippine Agricultural Engineering Standards and Specifications",
    "folder": "paes_standards",
    "materials": [
        {
            "title": "AMTEC: OFFICIAL WEBSITE",
            "file": "Official Website",
            "type": "link",
            "external_links": [
                {"name": "Review Materials", "url": "https://amtec.uplb.edu.ph/"},
                {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_Y4pRGu3x1tMGY4zJv0qK8"}
            ]
        },
        {
            "title": "Agricultural Structures",
            "file": "Agricultural Structures Official Link", 
            "type": "link",
            "external_links": [
                {"name": "Review Materials", "url": "https://amtec.uplb.edu.ph/agricultural-structures-u-c/"},
                {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk94OIklHPDKvsKu8aKofmye"}
            ]
        },
        {
            "title": "Engineering Materials",
            "file": "Engineering Materials Official Link", 
            "type": "link",
            "external_links": [
                {"name": "Review Materials", "url": "https://amtec.uplb.edu.ph/engineering-materials-u-c/"},
                {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_j2nmO4YeRA3C0siQ7Iv__"}
            ]
        },
        {
            "title": "Irrigation Structures",
            "file": "Irrigation Structures Official Link", 
            "type": "link",
            "external_links": [
                {"name": "Review Materials", "url": "https://amtec.uplb.edu.ph/irrigation-structures-u-d/"},
                {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_JZj0vWDbnZLiYXU5-eKgx"}
            ]
        },
        {
            "title": "Production Machinery",
            "file": "Production Machinery Official Link", 
            "type": "link",
            "external_links": [
                {"name": "Review Materials", "url": "https://amtec.uplb.edu.ph/production-machinery-2/"},
                {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk-9iCHUrJRBJw5TIDbmG0oQ"}
            ]
        },
        {
            "title": "Post-Harvest Machinery",
            "file": "Post-Harvest Machinery Official Link",
            "type": "link",
            "external_links": [
                {"name": "Review Materials", "url": "https://amtec.uplb.edu.ph/post-harvest-machinery-building-on-process/"},
                {"name": "AB Engineering Guild Videos", "url": "https://www.youtube.com/playlist?list=PLmhYenTivOk_TL7QrNUa9gRIGFyVHd6gW"}
            ]
        }
    ]
}

}

def ensure_topics_exist():
    """Ensure all topics from TOPIC_CONFIG exist in the database"""
    for topic_name, config in TOPIC_CONFIG.items():
        topic = Topic.query.filter_by(name=topic_name).first()
        if not topic:
            topic = Topic(
                name=topic_name,
                description=config["description"],
                icon="fas fa-folder",  # Default icon
                color="#4CAF50"  # Default color
            )
            db.session.add(topic)
            print(f"Created topic: {topic_name}")
    
    db.session.commit()

@reviewer_bp.route('/')
@login_required
def topics():
    try:
        # Ensure topics exist in database
        ensure_topics_exist()
        
        topics = Topic.query.all()
        
        # Update topic names and add configuration
        updated_topics = []
        for topic in topics:
            if topic.name in TOPIC_CONFIG:
                topic_config = TOPIC_CONFIG[topic.name]
                topic.display_name = topic_config["display_name"]
                topic.description = topic_config["description"]
                topic.folder = topic_config["folder"]
                topic.config_materials = topic_config["materials"]
            else:
                topic.display_name = topic.name
                topic.folder = topic.name.lower().replace(' ', '_')
                topic.config_materials = []
            
            updated_topics.append(topic)
        
        # ========== ADD THIS CODE ==========
        # Fetch ABELE links from database
        from app.models import ABELELink
        abele_links = {}
        for link in ABELELink.query.filter_by(is_active=True).order_by(ABELELink.display_order).all():
            abele_links[link.section_name] = link
        # ===================================
        
        return render_template('reviewer/topics.html', 
                              title='Reviewer', 
                              topics=updated_topics,
                              abele_links=abele_links)  # Pass to template
                              
    except Exception as e:
        flash('Error loading topics. Please try again.', 'error')
        print(f"Error in topics route: {e}")
        return redirect(url_for('main.dashboard'))

@reviewer_bp.route('/reviewer/<int:topic_id>')
@login_required
def topic_detail(topic_id):
    try:
        topic = Topic.query.get_or_404(topic_id)
        
        # Get topic configuration
        topic_config = TOPIC_CONFIG.get(topic.name, {})
        
        # IMPORTANT: Fetch material links from database for this topic
        from app.models import MaterialLink
        db_links = MaterialLink.query.filter_by(topic_name=topic.name).all()
        
        # Create lookup dictionary for quick access
        links_lookup = {}
        for link in db_links:
            key = f"{link.material_title}_{link.link_name}"
            links_lookup[key] = link
        
        # Add configuration to topic
        topic.display_name = topic_config.get("display_name", topic.name)
        topic.description = topic_config.get("description", topic.description)
        topic.folder = topic_config.get("folder", topic.name.lower().replace(' ', '_'))
        
        # Process config_materials and OVERRIDE hardcoded links with database links
        config_materials = topic_config.get("materials", [])
        for material in config_materials:
            material_title = material.get('title', '')
            
            # Get database links
            review_link = links_lookup.get(f"{material_title}_Review Materials")
            video_link = links_lookup.get(f"{material_title}_AB Engineering Guild Videos")
            
            # OVERRIDE the hardcoded external_links with database values
            # This way, the template continues to use material.external_links
            # but with the updated URLs from the database
            new_external_links = []
            
            # Add Review Materials link from database if exists
            if review_link and review_link.link_url and review_link.link_url != '#':
                new_external_links.append({
                    'name': 'Review Materials',
                    'url': review_link.link_url
                })
            else:
                # Fallback to hardcoded link
                for link in material.get('external_links', []):
                    if link.get('name') == 'Review Materials':
                        new_external_links.append(link)
                        break
            
            # Add Video link from database if exists
            if video_link and video_link.link_url and video_link.link_url != '#':
                new_external_links.append({
                    'name': 'AB Engineering Guild Videos',
                    'url': video_link.link_url
                })
            else:
                # Fallback to hardcoded link
                for link in material.get('external_links', []):
                    if link.get('name') == 'AB Engineering Guild Videos':
                        new_external_links.append(link)
                        break
            
            # Replace the external_links with our new list (database first, then hardcoded fallback)
            material['external_links'] = new_external_links
        
        topic.config_materials = config_materials
        
        return render_template('reviewer/topic_detail.html', 
                              title=topic.display_name, 
                              topic=topic)
                              
    except Exception as e:
        flash('Error loading topic details. Please try again.', 'error')
        print(f"Error in topic_detail route: {e}")
        return redirect(url_for('reviewer.topics'))

@reviewer_bp.route('/reviewer/download/<int:material_id>')
@login_required
def download_material(material_id):
    try:
        material = StudyMaterial.query.get_or_404(material_id)
        
        if material.file_path and os.path.exists(material.file_path):
            return send_file(material.file_path, as_attachment=True)
        else:
            flash('File not found', 'error')
            return redirect(url_for('reviewer.topic_detail', topic_id=material.topic_id))
    except Exception as e:
        flash('Error downloading file', 'error')
        return redirect(url_for('reviewer.topics'))

@reviewer_bp.route('/reviewer/view/<int:material_id>')
@login_required
def view_material(material_id):
    try:
        material = StudyMaterial.query.get_or_404(material_id)
        
        if material.file_path and os.path.exists(material.file_path):
            return send_file(material.file_path)
        else:
            flash('File not found', 'error')
            return redirect(url_for('reviewer.topic_detail', topic_id=material.topic_id))
    except Exception as e:
        flash('Error viewing file', 'error')
        return redirect(url_for('reviewer.topics'))

@reviewer_bp.route('/reviewer/search')
@login_required
def search_material():
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return redirect(url_for('reviewer.topics'))
    
    try:
        # Search in topics (database)
        topics = Topic.query.filter(
            (Topic.name.ilike(f'%{keyword}%')) | 
            (Topic.description.ilike(f'%{keyword}%'))
        ).all()
        
        # Search in TOPIC_CONFIG materials (the actual review materials)
        config_materials_results = []
        for topic_name, config in TOPIC_CONFIG.items():
            for material in config.get('materials', []):
                material_title = material.get('title', '')
                if keyword.lower() in material_title.lower():
                    config_materials_results.append({
                        'title': material_title,
                        'topic_name': topic_name,
                        'topic_display': TOPIC_CONFIG[topic_name]['display_name'],
                        'topic_id': Topic.query.filter_by(name=topic_name).first().id if Topic.query.filter_by(name=topic_name).first() else None
                    })
        
        # Search in PAES standards
        paes_standards = PAESStandard.query.filter(
            (PAESStandard.code.ilike(f'%{keyword}%')) | 
            (PAESStandard.title.ilike(f'%{keyword}%')) | 
            (PAESStandard.description.ilike(f'%{keyword}%'))
        ).all()
        
        return render_template('reviewer/search_results.html', 
                              title='Search Results',
                              keyword=keyword,
                              topics=topics,
                              config_materials=config_materials_results,
                              paes_standards=paes_standards)
                              
    except Exception as e:
        flash('Error searching materials', 'error')
        print(f"Search error: {e}")
        return redirect(url_for('reviewer.topics'))

@reviewer_bp.route('/paes')
@login_required
def paes_reference():
    paes_standards = PAESStandard.query.all()
    paes_subcategories = {
        "AREA I: ABELE REVIEW - QUIZ": "#",
        "AREA I: ABELE REVIEW - SOLVINGS": "#", 
        "AREA II: ABELE REVIEW - QUIZ": "#",
        "AREA II: ABELE REVIEW - SOLVINGS": "#",
        "AREA III: ABELE REVIEW - QUIZ": "#",
        "AREA III: ABELE REVIEW - SOLVINGS": "#",
        # Add more categories as needed
    }
    return render_template('reviewer/paes.html', 
                          title='PAES Standards', 
                          paes_standards=paes_standards,
                          paes_subcategories=paes_subcategories)

@reviewer_bp.route('/paes/search')
@login_required
def search_paes():
    code = request.args.get('code', '')
    
    if code:
        paes_standard = PAESStandard.query.filter(
            (PAESStandard.code.ilike(f'%{code}%')) | 
            (PAESStandard.title.ilike(f'%{code}%'))
        ).first()
        
        if paes_standard:
            return render_template('reviewer/paes_detail.html', 
                                  title=paes_standard.code,
                                  paes_standard=paes_standard)
        else:
            flash('PAES standard not found', 'warning')
    
    return redirect(url_for('reviewer.paes_reference'))

@reviewer_bp.route('/paes/download/<int:paes_id>')
@login_required
def download_paes(paes_id):
    try:
        paes_standard = PAESStandard.query.get_or_404(paes_id)
        
        if paes_standard.file_path and os.path.exists(paes_standard.file_path):
            return send_file(paes_standard.file_path, as_attachment=True)
        else:
            flash('PAES file not found', 'error')
            return redirect(url_for('reviewer.paes_reference'))
    except Exception as e:
        flash('Error downloading PAES file', 'error')
        return redirect(url_for('reviewer.paes_reference'))