from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
from models import db, User, Presentation as PresentationModel, Slide
from auth import auth_bp, login_required
from pptx_export import export_pptx_local
from text_extraction_utils import process_uploaded_file, analyze_text_content, chunk_text, detect_headings_and_structure
import model_downloader
from ollama_client import (
    generate_presentation_outline,
    generate_slides_from_outline,
    generate_presentation_outline_enhanced,
    generate_slides_from_outline_enhanced
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
                          fav_template=fav_template,
                          create_url=url_for('create'))
# Update your editor route in app.py
@app.route('/editor')
@login_required
def editor():
    # Check if this is a generated presentation
    generated = request.args.get('generated', 'false').lower() == 'true'
    return render_template('editor.html', generated=generated)

# Make sure your generate.html template exists and is being served
@app.route('/create/generate')
@login_required  
def generate_page():
    """Universal generation page based on method"""
    method = request.args.get('method', 'topic')
    
    if method not in ['topic', 'text', 'upload']:
        return redirect(url_for('create'))
    
    return render_template('generate.html', method=method)

# Ensure your outline generation endpoint works
@app.route('/api/generate-outline', methods=['POST'])
@login_required
def generate_outline_enhanced():
    """Enhanced outline generation supporting all input methods"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        slide_count = int(data.get('slideCount', 5))
        input_method = data.get('inputMethod', 'topic')
        
        logging.info(f"🎯 Generating outline: method={input_method}, topic='{topic}', slides={slide_count}")
        
        # Validate common requirements
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        if not (1 <= slide_count <= 10):
            return jsonify({'error': 'Slide count must be between 1 and 10'}), 400
        
        # Handle different input methods
        content_context = None
        processing_mode = 'generate'
        
        if input_method == 'text':
            text_content = data.get('textContent', '')
            text_stats = data.get('textStats', {})
            
            if not text_content or len(text_content.strip()) < 50:
                return jsonify({'error': 'Text content must be at least 50 characters'}), 400
            
            content_context = {
                'type': 'text',
                'content': text_content,
                'stats': text_stats,
                'word_count': len(text_content.split()),
                'char_count': len(text_content)
            }
            processing_mode = 'preserve'
            
        elif input_method == 'upload':
            document_content = data.get('documentContent', '')
            document_stats = data.get('documentStats', {})
            processing_mode = data.get('processingMode', 'preserve')
            
            if not document_content or len(document_content.strip()) < 50:
                return jsonify({'error': 'Document content must be at least 50 characters'}), 400
            
            content_context = {
                'type': 'document',
                'content': document_content,
                'stats': document_stats,
                'processing_mode': processing_mode,
                'word_count': len(document_content.split()),
                'char_count': len(document_content)
            }
        
        # Generate outline with content context
        outline = generate_presentation_outline_enhanced(
            topic=topic,
            slide_count=slide_count,
            input_method=input_method,
            content_context=content_context,
            processing_mode=processing_mode
        )
        
        if not outline:
            return jsonify({'error': 'Failed to generate outline'}), 500
        
        # Add generation metadata
        outline['generation_metadata'] = {
            'input_method': input_method,
            'processing_mode': processing_mode,
            'content_stats': content_context.get('stats', {}) if content_context else {},
            'generated_at': datetime.now().isoformat(),
            'slide_count_requested': slide_count,
            'slide_count_generated': len(outline.get('slide_structure', []))
        }
        
        logging.info(f"✅ Enhanced outline generated: {len(outline['slide_structure'])} slides from {input_method}")
        
        return jsonify({
            'outline': outline,
            'message': f'Outline generated successfully from {input_method}',
            'input_method': input_method,
            'processing_mode': processing_mode
        })
        
    except Exception as e:
        logging.error(f"❌ Error in enhanced outline generation: {e}")
        return jsonify({'error': f'Outline generation failed: {str(e)}'}), 500

# Ensure your slide generation from outline works
@app.route('/api/generate-from-outline', methods=['POST'])
@login_required
def generate_from_outline_enhanced():
    """Enhanced slide generation from outline with content context"""
    try:
        data = request.json
        outline = data.get('outline')
        template_id = data.get('template')
        content_data = data.get('contentData')  # Original content for context
        processing_mode = data.get('processingMode', 'preserve')
        
        if not outline or not template_id:
            return jsonify({'error': 'Outline and template are required'}), 400
        
        # Extract metadata
        generation_metadata = outline.get('generation_metadata', {})
        input_method = generation_metadata.get('input_method', 'topic')
        
        logging.info(f"🎨 Generating slides from outline: method={input_method}, slides={len(outline['slide_structure'])}")
        
        # Generate slides with enhanced context
        slides = generate_slides_from_outline_enhanced(
            outline=outline,
            template_id=template_id,
            content_data=content_data,
            processing_mode=processing_mode
        )
        
        if not slides:
            return jsonify({'error': 'Failed to generate slides from outline'}), 500
        
        logging.info(f"✅ Generated {len(slides)} slides from enhanced outline")
        
        return jsonify({
            'slides': slides,
            'template': template_id,
            'outline': outline,
            'slide_count': len(slides),
            'generation_method': f'{input_method}-outline-based',
            'processing_mode': processing_mode,
            'input_method': input_method,
            'content_preserved': content_data is not None
        })
        
    except Exception as e:
        logging.error(f"❌ Error generating slides from enhanced outline: {e}")
        return jsonify({'error': f'Slide generation failed: {str(e)}'}), 500

@app.route('/api/generate-presentation', methods=['POST'])
@login_required
def generate_presentation_new_flow():
    """Generate presentation using the new outline → theme → slides flow"""
    try:
        data = request.json
        method = data.get('method', 'topic')
        outline = data.get('outline')
        template_id = data.get('template')
        
        if not outline or not template_id:
            return jsonify({'error': 'Outline and template are required'}), 400
        
        # Generate slides from outline
        if method in ['text', 'upload'] and data.get('contentData'):
            # Use enhanced generation with content context
            slides = generate_slides_from_outline_enhanced(
                outline=outline,
                template_id=template_id,
                content_data=data.get('contentData'),
                processing_mode=data.get('processingMode', 'preserve')
            )
        else:
            # Use standard outline-based generation
            slides = generate_slides_from_outline(outline, template_id)
        
        if not slides:
            return jsonify({'error': 'Failed to generate slides from outline'}), 500
        
        return jsonify({
            'slides': slides,
            'template': template_id,
            'outline': outline,
            'slide_count': len(slides),
            'generation_method': f'{method}-outline-based',
            'success': True
        })
        
    except Exception as e:
        logging.error(f"Error in new presentation generation flow: {e}")
        return jsonify({'error': f'Presentation generation failed: {str(e)}'}), 500

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

# Add these routes to your app.py file


    
@app.route('/create')
@login_required
def create():
    """New landing page for method selection"""
    return render_template('create.html')


# Update your /api/process-headings route to handle the new heading-based splitting
@app.route('/api/process-headings', methods=['POST'])
@login_required
def process_headings():
    """Process text/document and detect headings for slides"""
    data = request.json
    content = data.get('content', '')
    method = data.get('method', 'text')
    processing_mode = data.get('processing_mode', 'preserve')
    
    try:
        if method == 'text':
            # Process text and detect headings
            slides_structure = detect_headings_and_structure(content)
        elif method == 'upload':
            # Process uploaded document
            slides_structure = detect_headings_and_structure(content)
        else:
            return jsonify({'error': 'Invalid method'}), 400
        
        return jsonify({
            'success': True,
            'slides': slides_structure,
            'method': method,
            'processing_mode': processing_mode,
            'slide_count': len(slides_structure),
            'detected_headings': len([s for s in slides_structure if s.get('is_heading', False)])
        })
        
    except Exception as e:
        logging.error(f"Error processing headings: {e}")
        return jsonify({'error': str(e)}), 500
    
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

