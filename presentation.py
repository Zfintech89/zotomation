# # presentations.py
# from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
# from models import db, Presentation, Slide, User
# from auth import login_required
# from datetime import datetime
# from ollama_client import generate_content

# pres_bp = Blueprint('presentations', __name__)

# @pres_bp.route('/save', methods=['POST'])
# @login_required
# def save_presentation():
#     user_id = session.get('user_id')
#     data = request.json
    
#     # Validate input
#     topic = data.get('topic')
#     template_id = data.get('template')
#     slides = data.get('slides', [])
#     slide_count = len(slides)
    
#     if not topic or not template_id or not slides:
#         return jsonify({'error': 'Missing required fields'}), 400
    
#     # Create presentation
#     presentation = Presentation(
#         user_id=user_id,
#         topic=topic,
#         template_id=template_id,
#         slide_count=slide_count
#     )
    
#     db.session.add(presentation)
#     db.session.flush()  # To get the presentation ID
    
#     # Add slides
#     for i, slide_data in enumerate(slides):
#         slide = Slide(
#             presentation_id=presentation.id,
#             slide_order=i,
#             layout=slide_data.get('layout'),
#             content=slide_data.get('content', {})
#         )
#         db.session.add(slide)
    
#     db.session.commit()
    
#     return jsonify({
#         'message': 'Presentation saved successfully',
#         'presentation': presentation.to_dict()
#     }), 201

# @pres_bp.route('/list', methods=['GET'])
# @login_required
# def list_presentations():
#     user_id = session.get('user_id')
    
#     # Get all presentations for the user
#     presentations = Presentation.query.filter_by(user_id=user_id).order_by(Presentation.updated_at.desc()).all()
    
#     return jsonify({
#         'presentations': [p.to_dict() for p in presentations]
#     })

# @pres_bp.route('/dashboard', methods=['GET'])
# @login_required
# def dashboard():
#     user_id = session.get('user_id')
#     username = session.get('username')
    
#     # Get all presentations for the user
#     presentations = Presentation.query.filter_by(user_id=user_id).order_by(Presentation.updated_at.desc()).all()
    
#     return render_template('dashboard.html', 
#                           username=username,
#                           presentations=presentations)

# @pres_bp.route('/<int:presentation_id>', methods=['GET'])
# @login_required
# def get_presentation(presentation_id):
#     user_id = session.get('user_id')
    
#     # Get the presentation
#     presentation = Presentation.query.filter_by(id=presentation_id, user_id=user_id).first()
    
#     if not presentation:
#         return jsonify({'error': 'Presentation not found'}), 404
    
#     return jsonify({
#         'presentation': presentation.to_dict()
#     })

# @pres_bp.route('/edit/<int:presentation_id>', methods=['GET'])
# @login_required
# def edit_presentation(presentation_id):
#     user_id = session.get('user_id')
    
#     # Get the presentation
#     presentation = Presentation.query.filter_by(id=presentation_id, user_id=user_id).first()
    
#     if not presentation:
#         return redirect(url_for('pres_bp.dashboard'))
    
#     # Convert to dict for the template
#     presentation_data = presentation.to_dict()
    
#     return render_template('editor.html', presentation=presentation_data)

# @pres_bp.route('/<int:presentation_id>', methods=['PUT'])
# @login_required
# def update_presentation(presentation_id):
#     user_id = session.get('user_id')
#     data = request.json
    
#     # Get the presentation
#     presentation = Presentation.query.filter_by(id=presentation_id, user_id=user_id).first()
    
#     if not presentation:
#         return jsonify({'error': 'Presentation not found'}), 404
    
#     # Update presentation fields
#     if 'topic' in data:
#         presentation.topic = data['topic']
    
#     if 'template' in data:
#         presentation.template_id = data['template']
    
#     if 'slides' in data:
#         # Delete existing slides
#         Slide.query.filter_by(presentation_id=presentation.id).delete()
        
#         # Add new slides
#         for i, slide_data in enumerate(data['slides']):
#             slide = Slide(
#                 presentation_id=presentation.id,
#                 slide_order=i,
#                 layout=slide_data.get('layout'),
#                 content=slide_data.get('content', {})
#             )
#             db.session.add(slide)
        
#         presentation.slide_count = len(data['slides'])
    
#     # Update timestamp
#     presentation.updated_at = datetime.utcnow()
    
#     db.session.commit()
    
#     return jsonify({
#         'message': 'Presentation updated successfully',
#         'presentation': presentation.to_dict()
#     })

# @pres_bp.route('/<int:presentation_id>', methods=['DELETE'])
# @login_required
# def delete_presentation(presentation_id):
#     user_id = session.get('user_id')
    
#     # Get the presentation
#     presentation = Presentation.query.filter_by(id=presentation_id, user_id=user_id).first()
    
#     if not presentation:
#         return jsonify({'error': 'Presentation not found'}), 404
    
#     # Delete the presentation
#     db.session.delete(presentation)
#     db.session.commit()
    
#     return jsonify({
#         'message': 'Presentation deleted successfully'
#     })