from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
from models import db, User, Presentation as PresentationModel, Slide
from auth import auth_bp, login_required
from pptx_export import export_pptx_local, hex_to_rgb, parse_template_colors, apply_template_to_slide, apply_text_formatting, clean_text_content
from text_extraction_utils import process_uploaded_file, analyze_text_content, chunk_text
import model_downloader
from ollama_client import (
    generate_content, 
    split_text_for_slides,
    generate_content_from_extracted_text
)
from content_utils import process_content_for_layout
import re
import os
import random
import json
import requests
import tempfile
import logging
import calendar
import textwrap

from datetime import datetime, timedelta, timezone as dt_timezone
from pytz import timezone as pytz_timezone
from collections import Counter
from sqlalchemy import func, extract, cast, Date

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

from tkinter import Tk, filedialog  


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generation.log"),
        logging.StreamHandler()
    ]
)
DEFAULT_DOCUMENT_MODE = 'preserve'  # Default mode for document processing
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pptgenerator.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.route('/api/export-local', methods=['POST'])(export_pptx_local)
@app.template_filter('format_datetime')
def format_datetime_filter(dt):
    """Format datetime for display."""
    if not dt:
        return ""
    return dt.strftime('%b %d, %Y - %I:%M %p')

@app.route('/api/model/status', methods=['GET'])
def model_status():
    status = model_downloader.get_status()
    return jsonify(status)

@app.route('/api/model/start-download', methods=['POST'])
def model_start_download():
    result = model_downloader.start_download()
    return jsonify(result)

def is_model_downloaded():
    return model_downloader.is_model_downloaded()

app.register_blueprint(auth_bp, url_prefix='/auth')

LAYOUTS = [
    "titleAndBullets",
    "quote",
    "imageAndParagraph",
    "twoColumn",
    "titleOnly",
    "imageWithFeatures",
    "numberedFeatures",
    "benefitsGrid",
    "iconGrid",
    "sideBySideComparison",
    "timeline",
    "conclusion"  

]

templates = {
    'corporate': {
        'colors': {
            'primary': '#0f4c81',
            'secondary': '#6e9cc4',
            'accent': '#f2b138',
            'background': '#ffffff',
            'text': '#333333'
        },
        'font': 'Arial'
    },
    'creative': {
        'colors': {
            'primary': '#ff6b6b',
            'secondary': '#4ecdc4',
            'accent': '#ffd166',
            'background': '#f9f1e6',
            'text': '#5a3921'
        },
        'font': 'Georgia'
    },
    'creative updated': {
        'colors': {
            'primary': '#3A86FF',
            'secondary': '#8338EC',
            'accent': '#00CFC1',
            'background': '#FDFDFD',
            'text': '#1D1D1D'
        },
        'font': 'Inter'
    },
    'minimal': {
        'colors': {
            'primary': '#2c3e50',
            'secondary': '#95a5a6',
            'accent': '#e74c3c',
            'background': '#f8f8f8',
            'text': '#222222'
        },
        'font': 'Helvetica'
    },
    'nature': {
        'colors': {
            'primary': '#2d6a4f',
            'secondary': '#74c69d',
            'accent': '#ffb703',
            'background': '#f1faee',
            'text': '#1b4332'
        },
        'font': 'Georgia'
    },
    'tech': {
        'colors': {
            'primary': '#3a0ca3',
            'secondary': '#4361ee',
            'accent': '#7209b7',
            'background': '#f8f9fa',
            'text': '#212529'
        },
        'font': 'Arial'
    },
    'gradient': {
        'colors': {
            'primary': '#8338ec',
            'secondary': '#3a86ff',
            'accent': '#ff006e',
            'background': '#ffffff',
            'text': '#2b2d42'
        },
        'font': 'Arial'
    },
    'energetic': {
        'colors': {
            'primary': '#f72585',
            'secondary': '#7209b7',
            'accent': '#4cc9f0',
            'background': '#ffffff',
            'text': '#2b2d42'
        },
        'font': 'Helvetica'
    },
    'earthy': {
        'colors': {
            'primary': '#996633',
            'secondary': '#dda15e',
            'accent': '#bc6c25',
            'background': '#fefae0',
            'text': '#283618'
        },
        'font': 'Georgia'
    },
    'ocean': {
        'colors': {
            'primary': '#003566',
            'secondary': '#468faf',
            'accent': '#00b4d8',
            'background': '#f0f7f9',
            'text': '#001845'
        },
        'font': 'Helvetica'
    },
    'monochrome': {
        'colors': {
            'primary': '#2b2d42',
            'secondary': '#8d99ae',
            'accent': '#ef233c',
            'background': '#edf2f4',
            'text': '#1a1a1a'
        },
        'font': 'Helvetica'
    },
    'sunset': {
        'colors': {
            'primary': '#ff9e00',
            'secondary': '#ff4d00',
            'accent': '#7678ed',
            'background': '#fff1e6',
            'text': '#3d405b'
        },
        'font': 'Georgia'
    },
    'botanical': {
        'colors': {
            'primary': '#386641',
            'secondary': '#a7c957',
            'accent': '#fb8500',
            'background': '#f8f9fa',
            'text': '#283618'
        },
        'font': 'Georgia'
    }
}

@app.route('/api/presentations/<int:presentation_id>/slides', methods=['POST', 'PUT', 'DELETE'])
@login_required
def manage_slides(presentation_id):
    """Endpoint for managing slides within a presentation"""
    user_id = session.get('user_id')
    presentation = PresentationModel.query.filter_by(id=presentation_id, user_id=user_id).first()
    
    if not presentation:
        return jsonify({'error': 'Presentation not found or unauthorized'}), 404
    
    if request.method == 'POST':
        data = request.json
        layout = data.get('layout', 'titleOnly')  
        
        content = generate_default_content(layout, presentation.topic)
        
        new_slide = Slide(
            presentation_id=presentation.id,
            slide_order=presentation.slide_count,  
            layout=layout,
            content=content
        )
        
        db.session.add(new_slide)
        presentation.slide_count += 1
        presentation.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Slide added successfully',
            'slide': new_slide.to_dict()
        })
        
    elif request.method == 'PUT':
        data = request.json
        
        if 'slides' in data:
            slides_data = data['slides']
            
            Slide.query.filter_by(presentation_id=presentation.id).delete()
            
            for i, slide_data in enumerate(slides_data):
                slide = Slide(
                    presentation_id=presentation.id,
                    slide_order=i,
                    layout=slide_data.get('layout'),
                    content=slide_data.get('content', {})
                )
                db.session.add(slide)
            
            presentation.slide_count = len(slides_data)
            
        elif 'slide_id' in data:
            slide_id = data['slide_id']
            slide = Slide.query.filter_by(id=slide_id, presentation_id=presentation.id).first()
            
            if not slide:
                return jsonify({'error': 'Slide not found'}), 404
            
            if 'layout' in data:
                slide.layout = data['layout']
            
            if 'content' in data:
                slide.content = data['content']
        
        presentation.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Slides updated successfully',
            'presentation': presentation.to_dict()
        })
        
    elif request.method == 'DELETE':
        data = request.json
        slide_id = data.get('slide_id')
        
        slide = Slide.query.filter_by(id=slide_id, presentation_id=presentation.id).first()
        
        if not slide:
            return jsonify({'error': 'Slide not found'}), 404
        
        deleted_order = slide.slide_order
        
        db.session.delete(slide)
        
        slides_to_update = Slide.query.filter(
            Slide.presentation_id == presentation.id,
            Slide.slide_order > deleted_order
        ).all()
        
        for s in slides_to_update:
            s.slide_order -= 1
        
        presentation.slide_count -= 1
        presentation.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Slide deleted successfully'
        })

def generate_default_content(layout, topic):
    """Generate default content for a slide layout"""
    defaults = {
        'titleOnly': {
            'title': topic,
            'subtitle': 'Presentation Overview'
        },
        'titleAndBullets': {
            'title': f'Key Points about {topic}',
            'bullets': [
                'First key point',
                'Second key point',
                'Third key point'
            ]
        },
        'quote': {
            'quote': f'Inspirational quote about {topic}',
            'author': 'Author Name'
        },
        'imageAndParagraph': {
            'title': f'About {topic}',
            'imageDescription': 'Image',
            'paragraph': f'Descriptive paragraph about {topic}'
        },
        'twoColumn': {
            'title': f'{topic} Overview',
            'column1Title': 'First Aspect',
            'column1Content': 'Content for first column',
            'column2Title': 'Second Aspect',
            'column2Content': 'Content for second column'
        },
        'imageWithFeatures': {
            'title': f'Features of {topic}',
            'imageDescription': 'Image',
            'features': [
                {'title': 'Feature 1', 'description': 'Description of feature 1'},
                {'title': 'Feature 2', 'description': 'Description of feature 2'},
                {'title': 'Feature 3', 'description': 'Description of feature 3'},
                {'title': 'Feature 4', 'description': 'Description of feature 4'}
            ]
        },
        'timeline': {
            'title': f'Evolution of {topic}',
            'events': [
                {'year': '2000', 'title': 'First Event', 'description': 'Description of first event'},
                {'year': '2010', 'title': 'Second Event', 'description': 'Description of second event'},
                {'year': '2020', 'title': 'Third Event', 'description': 'Description of third event'}
            ]
        }
    }
    
    return defaults.get(layout, {})

@app.route('/analytics')
@login_required
def analytics():
    user_id = session.get('user_id')
    username = session.get('username')
    
    presentation_count = PresentationModel.query.filter_by(user_id=user_id).count()
    
    thirty_days_ago = datetime.now().replace(tzinfo=None) - timedelta(days=30)
    recent_presentations = PresentationModel.query.filter_by(user_id=user_id)\
        .filter(PresentationModel.created_at >= thirty_days_ago)\
        .order_by(PresentationModel.created_at.desc()).all()
    
    all_presentations = PresentationModel.query.filter_by(user_id=user_id).all()
    
    template_usage = {}
    for p in all_presentations:
        if p.template_id not in template_usage:
            template_usage[p.template_id] = 0
        template_usage[p.template_id] += 1
    
    if presentation_count > 0:
        avg_slides = sum([p.slide_count for p in all_presentations]) / presentation_count
    else:
        avg_slides = 0
    
    days_data = [0] * 7  
    
    for p in all_presentations:
        if p.created_at:
            day_of_week = p.created_at.weekday()
            day_of_week = (day_of_week + 1) % 7
            days_data[day_of_week] += 1
    
    all_slides = []
    for pres in all_presentations:
        all_slides.extend(pres.slides)
    
    layout_usage = {}
    for slide in all_slides:
        if slide.layout not in layout_usage:
            layout_usage[slide.layout] = 0
        layout_usage[slide.layout] += 1
    
    twelve_months_ago = datetime.now().replace(tzinfo=None) - timedelta(days=365)
    
    current_date = datetime.now()
    months_labels = []
    monthly_counts = {}
    
    for i in range(11, -1, -1):  
        month_date = current_date - timedelta(days=30*i)
        month_label = month_date.strftime('%b %Y')
        months_labels.append(month_label)
        monthly_counts[month_label] = 0
    
    for presentation in all_presentations:
        if presentation.created_at:
            if presentation.created_at >= twelve_months_ago:
                month_label = presentation.created_at.strftime('%b %Y')
                if month_label in monthly_counts:
                    monthly_counts[month_label] += 1
    
    months_data = [monthly_counts.get(label, 0) for label in months_labels]
    
    edit_frequency = []
    for p in all_presentations:
        if p.created_at and p.updated_at:  
            time_diff = p.updated_at - p.created_at
            hours_since_creation = time_diff.total_seconds() / 3600
            if hours_since_creation > 0:
                edit_frequency.append({
                    'id': p.id,
                    'topic': p.topic,
                    'edits_per_hour': (p.slide_count / hours_since_creation) if hours_since_creation else 0
                })
    
    edit_frequency.sort(key=lambda x: x['edits_per_hour'], reverse=True)
    top_edited = edit_frequency[:5]  
    
    return render_template('analytics.html',
                          username=username,
                          presentation_count=presentation_count,
                          recent_presentations=recent_presentations,
                          avg_slides=round(avg_slides, 1),
                          template_usage=template_usage,
                          layout_usage=layout_usage,
                          days_data=days_data,
                          months_labels=months_labels,
                          months_data=months_data,
                          top_edited=top_edited)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    username = session.get('username')
    
    presentations = PresentationModel.query.filter_by(user_id=user_id).order_by(PresentationModel.updated_at.desc()).all()
    
    thirty_days_ago = datetime.now().replace(tzinfo=None) - timedelta(days=30)
    recent_count = PresentationModel.query.filter_by(user_id=user_id)\
        .filter(PresentationModel.created_at >= thirty_days_ago).count()
    
    fav_template = "None"
    if presentations:
        template_counts = Counter([p.template_id for p in presentations])
        if template_counts:
            fav_template = template_counts.most_common(1)[0][0]
    
    return render_template('dashboard.html', 
                          username=username,
                          presentations=presentations,
                          recent_count=recent_count,
                          fav_template=fav_template)

@app.route('/editor')
@login_required
def editor():
    return render_template('editor.html')

@app.route('/editor/<int:presentation_id>')
@login_required
def edit_presentation(presentation_id):
    user_id = session.get('user_id')
    presentation = PresentationModel.query.filter_by(id=presentation_id, user_id=user_id).first()
    
    if not presentation:
        return redirect(url_for('dashboard'))
    
    return render_template('editor.html', presentation=presentation.to_dict())

@app.route('/api/save', methods=['POST'])
@login_required
def save_presentation():
    user_id = session.get('user_id')
    data = request.json
    
    topic = data.get('topic')
    template_id = data.get('template')
    slides = data.get('slides', [])
    
    if not topic or not template_id or not slides:
        return jsonify({'error': 'Missing required fields'}), 400
    
    presentation = PresentationModel(
        user_id=user_id,
        topic=topic,
        template_id=template_id,
        slide_count=len(slides)
    )
    db.session.add(presentation)
    db.session.flush()  
    
    for i, slide_data in enumerate(slides):
        slide = Slide(
            presentation_id=presentation.id,
            slide_order=i,
            layout=slide_data.get('layout'),
            content=slide_data.get('content', {})
        )
        db.session.add(slide)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Presentation saved successfully',
        'presentation': presentation.to_dict()
    })

@app.route('/api/presentations', methods=['GET'])
@login_required
def list_presentations():
    user_id = session.get('user_id')
    
    presentations = PresentationModel.query.filter_by(user_id=user_id).order_by(PresentationModel.updated_at.desc()).all()
    
    return jsonify({
        'presentations': [p.to_dict() for p in presentations]
    })

@app.route('/api/presentations/<int:presentation_id>', methods=['GET'])
@login_required
def get_presentation(presentation_id):
    user_id = session.get('user_id')
    
    presentation = PresentationModel.query.filter_by(id=presentation_id, user_id=user_id).first()
    
    if not presentation:
        return jsonify({'error': 'Presentation not found'}), 404
    
    return jsonify({
        'presentation': presentation.to_dict()
    })

@app.route('/api/presentations/<int:presentation_id>', methods=['DELETE'])
@login_required
def delete_presentation(presentation_id):
    """Delete a presentation."""
    presentation = PresentationModel.query.get_or_404(presentation_id)
    
    if presentation.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        Slide.query.filter_by(presentation_id=presentation_id).delete()
        db.session.delete(presentation)
        db.session.commit()
        return jsonify({'message': 'Presentation deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/presentations/<int:presentation_id>/update', methods=['POST'])
@login_required
def update_existing_presentation(presentation_id):
    """Update an existing presentation"""
    user_id = session.get('user_id')
    data = request.json
    
    presentation = PresentationModel.query.filter_by(id=presentation_id, user_id=user_id).first()
    
    if not presentation:
        return jsonify({'error': 'Presentation not found or unauthorized'}), 404
    
    topic = data.get('topic')
    template_id = data.get('template')
    slides = data.get('slides', [])
    
    if not topic or not template_id or not slides:
        return jsonify({'error': 'Missing required fields'}), 400
    
    presentation.topic = topic
    presentation.template_id = template_id
    presentation.slide_count = len(slides)
    presentation.updated_at = datetime.now()
    
    Slide.query.filter_by(presentation_id=presentation.id).delete()
    
    for i, slide_data in enumerate(slides):
        slide = Slide(
            presentation_id=presentation.id,
            slide_order=i,
            layout=slide_data.get('layout'),
            content=slide_data.get('content', {})
        )
        db.session.add(slide)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Presentation updated successfully',
        'presentation': presentation.to_dict()
    })
    
@app.route('/edit/<int:presentation_id>', methods=['GET'])
@login_required
def edit_existing_presentation(presentation_id):
    """Load an existing presentation into the editor"""
    user_id = session.get('user_id')
    
    try:
        presentation = PresentationModel.query.filter_by(id=presentation_id, user_id=user_id).first()
        
        if not presentation:
            print(f"No presentation found with ID {presentation_id} for user {user_id}")
            return redirect(url_for('dashboard'))
        
        presentation_data = presentation.to_dict()
        
        # Debug logging
        print(f"Loading presentation: {presentation_data.get('topic')}")
        print(f"   Slides: {len(presentation_data.get('slides', []))}")
        
        # Ensure required fields
        if not presentation_data.get('template_id'):
            presentation_data['template_id'] = 'corporate'
            
        return render_template('editor.html', existing_presentation=presentation_data)
        
    except Exception as e:
        print(f"Error loading presentation: {e}")
        return redirect(url_for('dashboard'))

def generate_slides_from_analyzed_structure_with_mode(full_text, topic, template_id, slide_count, slide_structure, processing_mode='preserve'):
    """Generate slides based on Ollama's structural analysis with content preservation"""
    slides = []
    
    # FIX: Ensure slide_count is not None
    if slide_count is None:
        # Use slide_structure length as fallback
        if slide_structure and isinstance(slide_structure, list):
            slide_count = len(slide_structure)
        else:
            slide_count = 5  # Default fallback
    
    # FIX: Ensure slide_structure exists
    if not slide_structure or not isinstance(slide_structure, list):
        # Generate fallback structure
        slide_structure = generate_fallback_slide_structure(slide_count, topic)
    
    # Split text into sections based on determined slide count
    content_slides_needed = max(0, slide_count - 2)  # Exclude title and conclusion
    text_sections = split_text_for_slides(full_text, content_slides_needed) if content_slides_needed > 0 else []
    
    for structure_item in slide_structure:
        slide_number = structure_item.get('slide_number', 1)
        layout = structure_item.get('layout', 'titleOnly')
        purpose = structure_item.get('purpose', '')
        
        if layout == 'titleOnly':
            # Generate title slide using preserve mode
            content = generate_content_from_text('titleOnly', topic, full_text[:500], slide_number, slide_count, 'preserve')
            
            # Ensure title content
            if 'title' not in content or not content['title']:
                content['title'] = topic.capitalize()
            if 'subtitle' not in content or not content['subtitle']:
                content['subtitle'] = "Document Analysis and Key Insights"
            
            slides.append({
                'layout': 'titleOnly',
                'content': content
            })
            
        elif layout == 'conclusion':
            # Generate conclusion slide using source text
            conclusion_text = full_text[-1000:] if len(full_text) > 1000 else full_text
            content = generate_content_from_text(
                'conclusion', topic, conclusion_text, slide_number, slide_count, processing_mode
            )
            slides.append({
                'layout': 'conclusion',
                'content': content
            })
            
        else:
            # Generate content slide using appropriate text section with preservation
            section_index = slide_number - 2  # Adjust for title slide
            if section_index >= 0 and section_index < len(text_sections):
                section_text = text_sections[section_index]
            else:
                # Fallback to portion of full text
                portion_size = len(full_text) // max(1, content_slides_needed)
                start_pos = section_index * portion_size
                end_pos = min(len(full_text), start_pos + portion_size)
                section_text = full_text[start_pos:end_pos] if start_pos < len(full_text) else full_text
            
            content = generate_content_from_text(
                layout, topic, section_text, slide_number, slide_count, processing_mode
            )
            slides.append({
                'layout': layout,
                'content': content
            })
    
    logging.info(f"Generated {len(slides)} slides in {processing_mode} mode based on Ollama structure analysis")
    return slides

def generate_fallback_slide_structure(slide_count, topic):
    """Generate fallback slide structure when Ollama analysis fails"""
    available_layouts = [
        "titleAndBullets", "imageAndParagraph", "twoColumn",
        "imageWithFeatures", "numberedFeatures", "timeline"
    ]
    
    structure = []
    
    structure.append({
        "slide_number": 1,
        "layout": "titleOnly", 
        "purpose": "Introduction",
        "main_content": f"Title and overview of {topic}"
    })
    
    for i in range(2, slide_count):
        layout = available_layouts[(i-2) % len(available_layouts)]
        structure.append({
            "slide_number": i,
            "layout": layout,
            "purpose": f"Content section {i-1}",
            "main_content": f"Main topic {i-1} from document"
        })
    
    if slide_count > 2:
        structure.append({
            "slide_number": slide_count,
            "layout": "conclusion",
            "purpose": "Summary and conclusions", 
            "main_content": "Key takeaways and next steps"
        })
    
    return structure

from ollama_client import extract_clean_json, generate_content, generate_content_from_text

def generate_intelligent_slide_structure_fixed(slide_count, doc_structure):
    """Generate slide structure with better content distribution"""
    
    structure = []
    sections = list(doc_structure['key_sections'].keys())
    
    logging.info(f"Generating structure for {slide_count} slides with {len(sections)} sections")
    
    # Always start with title slide
    structure.append({
        "slide_number": 1,
        "layout": "titleOnly",
        "purpose": "Document title and overview"
    })
    
    # Determine content slides
    content_slides = slide_count - 2  # Exclude title and conclusion
    
    if content_slides > 0:
        # FIXED: Limit content slides to available unique sections
        max_content_slides = min(content_slides, len(sections))
        
        for i in range(max_content_slides):
            slide_num = i + 2
            
            # Choose layout based on content and position
            if i == 0 and doc_structure['paragraphs']:
                # First content slide as overview paragraph
                layout = "imageAndParagraph"
            elif len(sections) > i and sections[i] in doc_structure['bullet_sections']:
                # Use bullets if section has bullet points
                layout = "titleAndBullets"
            elif i == max_content_slides - 1 and max_content_slides > 1:
                # Last content slide as two-column
                layout = "twoColumn"
            else:
                # Default to bullets
                layout = "titleAndBullets"
            
            structure.append({
                "slide_number": slide_num,
                "layout": layout,
                "purpose": f"Content section: {sections[i] if i < len(sections) else 'Additional content'}"
            })
        
        # Adjust total slide count if we have fewer content slides
        actual_slide_count = max_content_slides + 2  # +2 for title and conclusion
    else:
        actual_slide_count = slide_count
    
    # Always end with conclusion if more than 2 slides
    if actual_slide_count > 2:
        structure.append({
            "slide_number": actual_slide_count,
            "layout": "conclusion",
            "purpose": "Summary and next steps"
        })
    
    logging.info(f"Final structure: {len(structure)} slides")
    return structure, actual_slide_count



@app.route('/api/generate-from-content', methods=['POST'])
def generate_from_content():
    try:
        data = request.json
        content_data = data.get('content')
        template_id = data.get('template')
        topic = data.get('topic', 'Document Summary')
        processing_mode = data.get('processing_mode', 'preserve')  # Get processing mode
        
        logging.info(f"🔄 Starting enhanced document processing: mode={processing_mode}, topic='{topic}'")
        
        if not content_data or not template_id:
            return jsonify({'error': 'Missing required data'}), 400
        
        full_text = content_data.get('full_text', '')
        
        if not full_text:
            return jsonify({'error': 'No text content found'}), 400
        
        # Clean text and validate
        meaningful_text = re.sub(r'\[Page \d+\]', '', full_text).strip()
        
        if len(meaningful_text) < 50:
            return jsonify({
                'error': 'Insufficient meaningful content extracted from document.',
                'extracted_length': len(meaningful_text)
            }), 400
        
        logging.info(f"📄 Processing {len(meaningful_text)} characters in {processing_mode} mode")
        
        # Use the enhanced document processing approach
        from ollama_client import generate_slides_from_full_document
        
        result = generate_slides_from_full_document(
            full_text=meaningful_text,
            topic=topic,
            template_id=template_id,
            processing_mode=processing_mode
        )
        
        slides = result['slides']
        document_analysis = result.get('document_analysis', {})
        
        if not slides:
            logging.error("❌ No slides generated from document")
            return jsonify({'error': 'Could not generate any valid slides from document content'}), 500
        
        # Prepare comprehensive response
        response_data = {
            'slides': slides,
            'template': template_id,
            'processing_mode': processing_mode,
            'slide_count': len(slides),
            'enhanced_analysis': {
                'document_analysis_success': result.get('document_analysis', {}).get('success', False),
                'recommended_slides': document_analysis.get('presentation_plan', {}).get('recommended_slides', len(slides)),
                'actual_slides': len(slides),
                'document_themes': document_analysis.get('document_analysis', {}).get('main_themes', []),
                'document_type': document_analysis.get('document_analysis', {}).get('document_type', 'document'),
                'complexity_level': document_analysis.get('document_analysis', {}).get('complexity_level', 'medium'),
                'processing_reasoning': document_analysis.get('presentation_plan', {}).get('reasoning', ''),
                'processing_mode_used': processing_mode
            }
        }
        
        # Log success details
        logging.info(f"✅ Enhanced document processing completed")
        logging.info(f"   - Mode: {processing_mode}")
        logging.info(f"   - Generated: {len(slides)} slides")
        logging.info(f"   - Document type: {document_analysis.get('document_analysis', {}).get('document_type', 'unknown')}")
        logging.info(f"   - Themes: {', '.join(document_analysis.get('document_analysis', {}).get('main_themes', []))}")
        
        # Log slide structure
        for i, slide in enumerate(slides, 1):
            layout = slide['layout']
            content_size = len(str(slide['content']))
            content_keys = list(slide['content'].keys())
            logging.info(f"   - Slide {i}: {layout} ({content_size} chars, keys: {content_keys})")
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"❌ Error in enhanced document processing: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Enhanced document processing failed: {str(e)}'}), 500

def validate_and_filter_slides(slides, source_text):
    """Validate slides and filter out low-quality ones"""
    
    quality_slides = []
    
    # Generic content patterns to avoid
    generic_patterns = [
        'column 1 content', 'column 2 content',
        'important benefit from document',
        'description of feature',
        'content for first column',
        'meeting documentation and key discussion points'
    ]
    
    for slide in slides:
        content = slide.get('content', {})
        layout = slide.get('layout', '')
        
        # Check for generic content
        is_generic = False
        content_str = str(content).lower()
        
        for pattern in generic_patterns:
            if pattern in content_str:
                logging.warning(f"Filtering out generic {layout} slide containing: {pattern}")
                is_generic = True
                break
        
        # Check for minimum content requirements
        has_meaningful_content = False
        
        if layout == 'titleOnly':
            has_meaningful_content = content.get('title') and len(content.get('title', '')) > 3
        elif layout == 'titleAndBullets':
            bullets = content.get('bullets', [])
            has_meaningful_content = len(bullets) >= 2 and all(len(str(b)) > 10 for b in bullets[:3])
        elif layout == 'imageAndParagraph':
            paragraph = content.get('paragraph', '')
            has_meaningful_content = len(paragraph) > 50
        elif layout == 'twoColumn':
            col1 = content.get('column1Content', '')
            col2 = content.get('column2Content', '')
            has_meaningful_content = len(col1) > 20 and len(col2) > 20
        elif layout == 'conclusion':
            summary = content.get('summary', '')
            next_steps = content.get('nextSteps', [])
            has_meaningful_content = len(summary) > 20 or len(next_steps) >= 2
        else:
            has_meaningful_content = True  # Accept other layouts
        
        if not is_generic and has_meaningful_content:
            quality_slides.append(slide)
        else:
            logging.info(f"Filtered out {layout} slide - Generic: {is_generic}, Meaningful: {has_meaningful_content}")
    
    return quality_slides

def generate_slides_from_analyzed_structure(full_text, topic, template_id, slide_count, slide_structure):
    """Generate slides based on Ollama's structural analysis"""
    slides = []
    
    # Split text into sections based on determined slide count
    text_sections = split_text_for_slides(full_text, slide_count - 2)  # Exclude title and conclusion
    
    for structure_item in slide_structure:
        slide_number = structure_item['slide_number']
        layout = structure_item['layout']
        purpose = structure_item['purpose']
        
        if layout == 'titleOnly':
            # Generate title slide
            content = generate_content('titleOnly', topic, slide_index=slide_number, total_slides=slide_count)
            content['topic'] = topic
            processed_content = process_content_for_layout(content, 'titleOnly')
            
            # Ensure title content
            if 'title' not in processed_content or not processed_content['title']:
                processed_content['title'] = topic.capitalize()
            if 'subtitle' not in processed_content or not processed_content['subtitle']:
                processed_content['subtitle'] = "Generated from Document Analysis"
            
            slides.append({
                'layout': 'titleOnly',
                'content': processed_content
            })
            
        elif layout == 'conclusion':
            # Generate conclusion slide using full text
            content = generate_content_from_extracted_text(
                'conclusion', topic, full_text, slide_number, slide_count
            )
            slides.append({
                'layout': 'conclusion',
                'content': content
            })
            
        else:
            # Generate content slide using appropriate text section
            section_index = slide_number - 2  # Adjust for title slide
            section_text = text_sections[section_index] if section_index < len(text_sections) else full_text
            
            content = generate_content_from_extracted_text(
                layout, topic, section_text, slide_number, slide_count
            )
            slides.append({
                'layout': layout,
                'content': content
            })
    
    logging.info(f"Generated {len(slides)} slides based on Ollama structure analysis")
    return slides

# Update the process-document route to remove slide count from response
@app.route('/api/process-document', methods=['POST'])
def process_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Process the uploaded file
        with tempfile.TemporaryDirectory() as temp_dir:
            result, error = process_uploaded_file(file, temp_dir)
            
            if error:
                return jsonify({'error': error}), 400
            
            # Convert chunks generator to list once
            chunks = list(chunk_text(result['text']))
            
            # Structure the content for slide generation
            structured_content = {
                'full_text': result['text'],
                'analysis': result['analysis'],
                'chunks': chunks,
                'processing_method': 'document_upload',
                'file_info': {
                    'original_filename': result['original_filename'],
                    'file_type': result['file_type']
                }
            }
            
            return jsonify({
                'success': True,
                'content': structured_content,
                'extracted_text': result['text'],
                # NOTE: Removed 'suggested_slides' - Ollama will determine this
                'file_info': {
                    'filename': result['original_filename'],
                    'type': result['file_type']
                },
                'stats': {
                    'characters': result['analysis']['chars'],
                    'words': result['analysis']['words'],
                    'sentences': result['analysis']['sentences'],
                    'paragraphs': result['analysis']['paragraphs'],
                    'chunks': len(chunks),
                    'readability': result['analysis']['readability']
                },
                'message': 'Document processed successfully. Ollama will determine optimal slide count.'
            })
            
    except Exception as e:
        logging.error(f"Error processing document: {e}")
        return jsonify({'error': f'Document processing failed: {str(e)}'}), 500

@app.route('/api/process-text', methods=['POST'])
def process_text_content():
    """Process pasted text content for presentation generation"""
    try:
        data = request.json
        text_content = data.get('text', '').strip()
        
        if not text_content:
            return jsonify({'error': 'No text content provided'}), 400
        
        if len(text_content) < 50:
            return jsonify({'error': 'Text content too short (minimum 50 characters)'}), 400
        
        # Analyze the text
        analysis = analyze_text_content(text_content)
        
        # Create chunks for better processing
        chunks = list(chunk_text(text_content))
        
        # Structure the content for slide generation
        structured_content = {
            'full_text': text_content,
            'analysis': analysis,
            'chunks': chunks,
            'processing_method': 'text_input'
        }
        
        return jsonify({
            'success': True,
            'content': structured_content,
            # NOTE: Removed 'suggested_slides' - Ollama will determine this
            'stats': {
                'characters': analysis['chars'],
                'words': analysis['words'],
                'sentences': analysis['sentences'],
                'paragraphs': analysis['paragraphs'],
                'chunks': len(chunks),
                'readability': analysis['readability']
            },
            'message': 'Text processed successfully. Ollama will determine optimal slide count.'
        })
        
    except Exception as e:
        logging.error(f"Error processing text content: {e}")
        return jsonify({'error': f'Text processing failed: {str(e)}'}), 500

@app.route('/api/generate', methods=['POST'])
@login_required
def generate():
    data = request.json
    template = data.get('template')
    topic = data.get('topic')
    slide_count = data.get('slideCount', 6)
    
    logging.info(f" GENERATE REQUEST: topic='{topic}', slideCount={slide_count}, template='{template}'")
    
    slide_count = min(max(1, int(slide_count)), 10)
    logging.info(f"Validated slide_count: {slide_count}")
    
    slides = []
    
    if slide_count == 1:
        title_content = generate_content('titleOnly', topic, slide_index=1, total_slides=1)
        title_content['topic'] = topic  # Add topic for processing
        processed_title_content = process_content_for_layout(title_content, 'titleOnly')
        
        if 'title' not in processed_title_content or not processed_title_content['title']:
            processed_title_content['title'] = f"{topic.capitalize()}"
        if 'subtitle' not in processed_title_content or not processed_title_content['subtitle']:
            processed_title_content['subtitle'] = "An In-depth Overview"
        
        slides.append({
            'layout': 'titleOnly',
            'content': processed_title_content
        })
        
        logging.info(f"Generated {len(slides)} slides for slide_count=1")
        return jsonify({'slides': slides, 'template': template})
    
    if slide_count == 2:
        # Title slide
        title_content = generate_content('titleOnly', topic, slide_index=1, total_slides=2)
        title_content['topic'] = topic
        processed_title_content = process_content_for_layout(title_content, 'titleOnly')
        
        if 'title' not in processed_title_content or not processed_title_content['title']:
            processed_title_content['title'] = f"{topic.capitalize()}"
        if 'subtitle' not in processed_title_content or not processed_title_content['subtitle']:
            processed_title_content['subtitle'] = "An In-depth Overview"
        
        slides.append({
            'layout': 'titleOnly',
            'content': processed_title_content
        })
        
        conclusion_content = generate_content('conclusion', topic, slide_index=2, total_slides=2)
        conclusion_content['topic'] = topic
        processed_conclusion_content = process_content_for_layout(conclusion_content, 'conclusion')
        
        slides.append({
            'layout': 'conclusion',
            'content': processed_conclusion_content
        })
        
        logging.info(f"Generated {len(slides)} slides for slide_count=2 (title + conclusion)")
        return jsonify({'slides': slides, 'template': template})
        
    # Continue with rest of the generate function...
    title_content = generate_content('titleOnly', topic, slide_index=1, total_slides=slide_count)
    title_content['topic'] = topic
    processed_title_content = process_content_for_layout(title_content, 'titleOnly')
    
    if 'title' not in processed_title_content or not processed_title_content['title']:
        processed_title_content['title'] = f"{topic.capitalize()}"
    if 'subtitle' not in processed_title_content or not processed_title_content['subtitle']:
        processed_title_content['subtitle'] = "An In-depth Overview"
    
    slides.append({
        'layout': 'titleOnly',
        'content': processed_title_content
    })
    
    content_slides_needed = slide_count - 2  
    
    available_layouts = [layout for layout in LAYOUTS if layout not in ['titleOnly', 'conclusion']]
    random.shuffle(available_layouts)
    
    for i in range(content_slides_needed):
        slide_position = i + 2  
        
        layout = available_layouts[i % len(available_layouts)]
        
        content = generate_content(layout, topic, slide_index=slide_position, total_slides=slide_count)
        content['topic'] = topic
        
        if isinstance(content, dict) and content.get("unsuitable_layout"):
            logging.info(f"Substituting unsuitable layout '{layout}' for topic '{topic}'")
            substitute_layouts = ["imageAndParagraph", "titleAndBullets", "quote"]
            substitute_layout = substitute_layouts[i % len(substitute_layouts)]
            content = generate_content(substitute_layout, topic, slide_index=slide_position, total_slides=slide_count)
            content['topic'] = topic
            layout = substitute_layout
        
        processed_content = process_content_for_layout(content, layout)
        
        slides.append({
            'layout': layout,
            'content': processed_content
        })
    
    conclusion_content = generate_content('conclusion', topic, slide_index=slide_count, total_slides=slide_count)
    conclusion_content['topic'] = topic
    processed_conclusion_content = process_content_for_layout(conclusion_content, 'conclusion')
    
    slides.append({
        'layout': 'conclusion',
        'content': processed_conclusion_content
    })
    
    logging.info(f"Generated {len(slides)} slides (expected: {slide_count})")
    logging.info(f"Structure: Title + {content_slides_needed} content slides + Conclusion")
    
    return jsonify({
        'slides': slides,
        'template': template
    })

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

