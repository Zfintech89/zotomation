import requests
import json
import logging
import os
import re  # ADD THIS MISSING IMPORT
from datetime import datetime
from content_utils import process_content_for_layout
import re
from collections import defaultdict



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
debug_dir = "error_logs"
os.makedirs(debug_dir, exist_ok=True)
logger = logging.getLogger("ollama_client")

OLLAMA_API_URL = "http://localhost:11434/api/generate"

PROCESSING_MODES = {
    'preserve': {
        'name': 'Preserve Original Content',
        'description': 'Keep original text structure and wording as much as possible',
        'instruction': 'Extract and format the content while preserving the original wording, facts, and structure. Keep key phrases, statistics, and important details exactly as written.',
        'temperature': 0.1,  
        'top_p': 0.7,
        'max_changes': 0.15  
    },
    'condense': {
        'name': 'Condense Key Points',
        'description': 'Summarize while maintaining core message and key facts',
        'instruction': 'Condense and summarize the content while preserving all key facts, statistics, and main ideas. Make it more concise but keep the essential information.',
        'temperature': 0.2, 
        'top_p': 0.8,
        'max_changes': 0.4 
    },
    'generate': {
        'name': 'Generate Enhanced Content',
        'description': 'Expand and enhance content with additional context and examples',
        'instruction': 'Use the content as a foundation to create enhanced, engaging presentation material. Expand on key ideas, add relevant context, and make it more compelling while staying true to the core message.',
        'temperature': 0.3, 
        'top_p': 0.9,
        'max_changes': 0.7 
    }
}

CONTENT_PRESERVATION_MODES = {
    'preserve': {
        'instruction': 'Format the following text into the required structure while preserving the original wording as much as possible. Keep key phrases, statistics, and important details exactly as written.',
        'max_changes': 0.1  # Allow only 10% content modification
    },
    'condense': {
        'instruction': 'Summarize the following text into the required structure while maintaining the core message and key facts.',
        'max_changes': 0.3  # Allow 30% content modification
    },
    'generate': {
        'instruction': 'Use the following text as inspiration to generate new slide content that enhances and expands on the ideas presented.',
        'max_changes': 0.7  # Allow 70% content modification
    }
}

DEFAULT_DOCUMENT_MODE = 'preserve'  


def extract_clean_json(text, context=""):
    """Enhanced JSON extraction"""
    if not text:
        return None
    
    # Clean up text
    text = text.strip()
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = re.sub(r'^[^{]*(?={)', '', text)
    text = re.sub(r'}[^}]*$', '}', text)
    
    try:
        # Try direct parsing
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError:
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed
            except json.JSONDecodeError:
                pass
    
    logger.warning(f"Failed to parse JSON for {context}")
    return None


def generate_with_ai_modes(layout, topic, source_text, slide_index, total_slides, processing_mode):
    """AI generation for condense and generate modes with proper prompts"""
    
    # Limit text for AI processing
    limited_text = source_text[:2000] if len(source_text) > 2000 else source_text
    
    # Mode-specific instructions
    if processing_mode == 'condense':
        mode_instruction = """CONDENSE and SUMMARIZE the following content into concise, clear points. 
Keep the core message but make it more brief and focused. Remove redundant information."""
        
    elif processing_mode == 'generate':
        mode_instruction = """USE the following content as INSPIRATION to create enhanced, engaging slide content. 
Expand on the ideas, add relevant context, and make it more compelling while staying true to the core message."""
    
    # Create layout-specific prompts with proper JSON structure
    layout_prompts = {
        'titleOnly': f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

TASK: Create a compelling title slide.

Return ONLY this JSON structure:
{{"title": "Engaging title (max 60 chars)", "subtitle": "Descriptive subtitle (max 120 chars)"}}

Example: {{"title": "System Optimization Review", "subtitle": "Enhancing Performance and User Experience"}}
""",

        'titleAndBullets': f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

TASK: Create 3-5 bullet points for this slide.

Return ONLY this JSON structure:
{{"title": "Clear slide title (max 80 chars)", "bullets": ["Point 1 (max 150 chars)", "Point 2 (max 150 chars)", "Point 3 (max 150 chars)"]}}

Example: {{"title": "Key System Improvements", "bullets": ["Enhanced speaker classification accuracy", "Streamlined content generation process", "Improved batch processing capabilities"]}}
""",

        'imageAndParagraph': f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

TASK: Create descriptive content with a paragraph.

Return ONLY this JSON structure:
{{"title": "Descriptive title (max 80 chars)", "imageDescription": "Professional image description", "paragraph": "Detailed paragraph (max 400 chars)"}}

Example: {{"title": "Meeting Outcomes", "imageDescription": "Professional team meeting in modern conference room", "paragraph": "The comprehensive review session identified critical system bottlenecks and established clear improvement pathways for enhanced performance."}}
""",

        'twoColumn': f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

TASK: Split content into two complementary sections.

Return ONLY this JSON structure:
{{"title": "Comparison title", "column1Title": "Left section", "column1Content": "Left content (max 300 chars)", "column2Title": "Right section", "column2Content": "Right content (max 300 chars)"}}

Example: {{"title": "System Analysis Overview", "column1Title": "Challenges Identified", "column1Content": "Processing delays, accuracy issues, and user experience gaps were identified as primary concerns requiring immediate attention.", "column2Title": "Solutions Implemented", "column2Content": "Advanced algorithms, batch processing optimization, and enhanced user feedback systems have been successfully deployed."}}
""",

        'conclusion': f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

TASK: Create a conclusion with actionable next steps.

Return ONLY this JSON structure:
{{"title": "Conclusion title", "summary": "Brief summary (max 200 chars)", "nextSteps": ["Action 1 (max 50 chars)", "Action 2 (max 50 chars)", "Action 3 (max 50 chars)"]}}

Example: {{"title": "Path Forward", "summary": "Successful system optimization achieved through collaborative effort and strategic improvements across all key areas.", "nextSteps": ["Monitor system performance", "Gather user feedback", "Plan next optimization cycle"]}}
""",

        'timeline': f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

TASK: Create a timeline of key developments or phases.

Return ONLY this JSON structure:
{{"title": "Timeline title", "events": [{{"year": "2024", "title": "Event name", "description": "Event description"}}, {{"year": "2025", "title": "Current phase", "description": "Current status"}}]}}

Example: {{"title": "Development Timeline", "events": [{{"year": "Q1 2024", "title": "Issue Identification", "description": "Comprehensive system analysis revealed key improvement areas"}}, {{"year": "Q2 2024", "title": "Solution Development", "description": "Advanced algorithms and processing methods implemented"}}, {{"year": "Current", "title": "Optimization Phase", "description": "Ongoing monitoring and fine-tuning of system performance"}}]}}
"""
    }
    
    prompt = layout_prompts.get(layout, f"""
{mode_instruction}

SOURCE CONTENT:
{limited_text}

Create appropriate {layout} content and return valid JSON only.
""")
    
    try:
        logger.debug(f"Attempting AI generation for {layout} in {processing_mode} mode")
        
        # Configure AI parameters based on mode
        if processing_mode == 'condense':
            temperature = 0.1  # More focused for condensing
            top_p = 0.8
        else:  # generate mode
            temperature = 0.3  # More creative for generation
            top_p = 0.9
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            logger.debug(f"AI response length: {len(generated_text)} chars")
            logger.debug(f"AI response preview: {generated_text[:200]}")
            
            # Extract JSON from response
            content_result = extract_clean_json(generated_text, layout)
            
            if content_result:
                logger.info(f"Successfully parsed AI JSON for {layout}")
                
                # Validate content quality
                if validate_ai_content_quality(content_result, layout, source_text):
                    # Process through content utils
                    content_result['topic'] = topic
                    content_result['slide_index'] = slide_index
                    content_result['total_slides'] = total_slides
                    content_result['processing_mode'] = processing_mode
                    
                    return process_content_for_layout(content_result, layout)
                else:
                    logger.warning(f"AI content quality validation failed for {layout}")
            else:
                logger.warning(f"Failed to parse AI JSON response for {layout}")
                logger.debug(f"Raw response: {generated_text}")
        else:
            logger.error(f"AI API error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error in AI generation: {e}")
    
    return None  # Signal failure to caller

def validate_ai_content_quality(content, layout, source_text):
    """Validate that AI-generated content is good quality and not generic"""
    
    if not isinstance(content, dict):
        return False
    
    # Check for generic content patterns
    generic_patterns = [
        'column 1 content', 'column 2 content', 'description of',
        'example of', 'placeholder for', 'content goes here',
        'insert content here', 'add content', 'sample text'
    ]
    
    content_str = str(content).lower()
    for pattern in generic_patterns:
        if pattern in content_str:
            logger.warning(f"Generic pattern detected: {pattern}")
            return False
    
    # Layout-specific validation
    if layout == 'titleOnly':
        return (content.get('title') and len(content.get('title', '')) > 5 and
                content.get('subtitle') and len(content.get('subtitle', '')) > 10)
    
    elif layout == 'titleAndBullets':
        bullets = content.get('bullets', [])
        return (content.get('title') and len(content.get('title', '')) > 5 and
                len(bullets) >= 3 and all(len(str(b)) > 15 for b in bullets[:3]))
    
    elif layout == 'imageAndParagraph':
        paragraph = content.get('paragraph', '')
        return (content.get('title') and len(content.get('title', '')) > 5 and
                len(paragraph) > 50)
    
    elif layout == 'twoColumn':
        col1 = content.get('column1Content', '')
        col2 = content.get('column2Content', '')
        return (content.get('title') and len(content.get('title', '')) > 5 and
                len(col1) > 30 and len(col2) > 30)
    
    elif layout == 'conclusion':
        summary = content.get('summary', '')
        next_steps = content.get('nextSteps', [])
        return (content.get('title') and len(content.get('title', '')) > 5 and
                (len(summary) > 20 or len(next_steps) >= 2))
    
    # Default validation
    return True

def clean_content_result(content_result, layout):
    """Remove any unexpected fields from the content result and clean titles"""
    if not isinstance(content_result, dict):
        return content_result
    
    if "unsuitable_layout" in content_result:
        return content_result
    
    # Clean titles by removing unwanted patterns
    if 'title' in content_result:
        content_result['title'] = clean_title(content_result['title'])
    
    # Clean other title fields
    title_fields = ['column1Title', 'column2Title', 'leftTitle', 'rightTitle']
    for field in title_fields:
        if field in content_result:
            content_result[field] = clean_title(content_result[field])
    
    # Clean feature/benefit/category titles
    if 'features' in content_result and isinstance(content_result['features'], list):
        for feature in content_result['features']:
            if isinstance(feature, dict) and 'title' in feature:
                feature['title'] = clean_title(feature['title'])
    
    if 'benefits' in content_result and isinstance(content_result['benefits'], list):
        for benefit in content_result['benefits']:
            if isinstance(benefit, dict) and 'title' in benefit:
                benefit['title'] = clean_title(benefit['title'])
    
    if 'categories' in content_result and isinstance(content_result['categories'], list):
        for category in content_result['categories']:
            if isinstance(category, dict) and 'name' in category:
                category['name'] = clean_title(category['name'])
    
    if 'events' in content_result and isinstance(content_result['events'], list):
        for event in content_result['events']:
            if isinstance(event, dict) and 'title' in event:
                event['title'] = clean_title(event['title'])
    
    expected_fields = {
        "titleOnly": ["title", "subtitle"],
        "titleAndBullets": ["title", "bullets"],
        "quote": ["quote", "author"],
        "imageAndParagraph": ["title", "imageDescription", "paragraph"],
        "twoColumn": ["title", "column1Title", "column1Content", "column2Title", "column2Content"],
        "imageWithFeatures": ["title", "imageDescription", "features"],
        "numberedFeatures": ["title", "imageDescription", "features"],
        "benefitsGrid": ["title", "imageDescription", "benefits"],
        "iconGrid": ["title", "categories"],
        "sideBySideComparison": ["title", "leftTitle", "rightTitle", "leftPoints", "rightPoints"],
        "timeline": ["title", "events"],
        "conclusion": ["title", "summary", "nextSteps"]
    }
    
    allowed_management_fields = ["slide_index", "total_slides"]
    
    if layout in expected_fields:
        if layout == "iconGrid":
            logger.debug("Validating iconGrid content")
            content_result = validate_and_fix_icon_grid(content_result, content_result.get('title', ''))
        elif layout == "numberedFeatures":
            logger.debug("Validating numberedFeatures content")
            content_result = validate_and_fix_numbered_features(content_result, content_result.get('title', ''))
            
        allowed_fields = expected_fields[layout] + allowed_management_fields
        return {k: v for k, v in content_result.items() if k in allowed_fields}
    
    return content_result

def clean_title(title):
    """Clean title by removing unwanted patterns like slide numbers, context prefixes, etc."""
    if not title or not isinstance(title, str):
        return title
    
    title = re.sub(r'\s*\(\d+\)\s*$', '', title)
    
    unwanted_prefixes = [
        'examples ', 'example ', 'statistics ', 'benefits ', 'challenges ',
        'applications ', 'history ', 'trends ', 'implementation ',
        'overview ', 'conclusion ', 'first ', 'second ', 'third ', 'fourth ',
        'key ', 'main ', 'primary ', 'secondary '
    ]
    
    title_lower = title.lower()
    for prefix in unwanted_prefixes:
        if title_lower.startswith(prefix):
            potential_title = title[len(prefix):].strip()
            if potential_title and len(potential_title) > 3:
                title = potential_title[0].upper() + potential_title[1:] if len(potential_title) > 1 else potential_title.upper()
    
    title = ' '.join(title.split())  
    title = title.strip()
    
    return title


def create_contextual_image_prompt(layout, topic, slide_content, slide_context):
    """Create detailed, comprehensive image prompt based on actual slide content"""
    
    template_colors = {
        'primary': '#0f4c81',
        'secondary': '#6e9cc4', 
        'accent': '#f2b138',
        'background': '#ffffff',
        'text': '#333333'
    }
    
    slide_content_text = format_slide_content_for_prompt(slide_content, layout)
    
    detailed_prompt = f"""You are an expert AI image prompt generator for professional PowerPoint presentations. 

SLIDE CONTENT CONTEXT:
Topic: {topic}
Layout Type: {layout}
Slide Context: {slide_context}

COMPLETE SLIDE CONTENT:
{slide_content_text}

YOUR TASK:
Generate an extremely detailed, comprehensive image description for this specific slide that will be used to create a professional PowerPoint image using AI image generation tools like Midjourney or DALL-E.

CRITICAL REQUIREMENT: Your response must be a highly detailed, comprehensive image description between 300-1000 characters. Be extremely specific about every visual element - describe objects, people, settings, lighting, colors, composition, mood, and atmosphere in rich detail. The more specific and detailed you are, the better the resulting image will be.

MANDATORY VISUAL REQUIREMENTS:
1. COLOR SCHEME INTEGRATION:
   - Primary color {template_colors['primary']} (deep professional blue) - use for main subjects, headers, key focal points
   - Secondary color {template_colors['secondary']} (medium blue) - use for supporting elements, backgrounds, secondary objects
   - Accent color {template_colors['accent']} (golden yellow) - use for highlights, call-to-action elements, important details
   - Background color {template_colors['background']} (clean white) - use for clean spaces, negative areas
   - Text color {template_colors['text']} (dark gray) - use for fine details, outlines, subtle elements

2. PROFESSIONAL DESIGN STANDARDS:
   - Ultra-high quality, presentation-ready imagery
   - Clean, modern, corporate aesthetic
   - Excellent contrast and readability
   - 16:9 widescreen aspect ratio
   - Professional lighting with soft shadows
   - Minimal noise, crisp details
   - Business-appropriate imagery only

3. COMPOSITION REQUIREMENTS:
   - Strategic negative space for text overlay areas
   - Clear visual hierarchy and focal points
   - Balanced composition following rule of thirds
   - Appropriate depth of field
   - Consistent perspective and scale
   - Visual flow that guides the eye naturally

4. CONTENT-SPECIFIC VISUALIZATION:
   Based on the slide content provided above, create extremely detailed imagery that:
   - Directly relates to and supports the written content with specific visual elements
   - Visualizes the key concepts, benefits, or processes mentioned with concrete objects and scenes
   - Uses appropriate metaphors and symbols that clearly represent the subject matter
   - Matches the tone and professionalism of the text with specific environmental details
   - Enhances understanding of the slide's message through rich visual storytelling
   - Includes specific details about people's expressions, clothing, body language if applicable
   - Describes exact objects, tools, equipment, or technology relevant to the topic
   - Specifies the setting/environment in detail (office, laboratory, outdoor scene, etc.)

5. TECHNICAL SPECIFICATIONS:
   - Photorealistic quality or high-end 3D rendering
   - Proper exposure and color balance
   - Sharp focus on main subjects
   - Professional studio lighting setup
   - Clean, uncluttered composition
   - Scalable elements that work at different sizes

6. CONTEXTUAL ELEMENTS TO INCLUDE (BE EXTREMELY SPECIFIC):
   - Industry-appropriate settings and environments (describe the exact type of office, laboratory, factory, etc.)
   - Relevant technology, tools, or equipment with specific brand-neutral details
   - Professional people in business contexts with detailed descriptions of their appearance, clothing, and actions
   - Abstract or conceptual elements that support the message with specific visual metaphors
   - Visual metaphors that enhance comprehension with concrete symbolic representations
   - Specific lighting conditions (natural window light, professional studio lighting, warm ambient lighting, etc.)
   - Detailed background elements that support the narrative
   - Specific textures, materials, and surfaces visible in the scene
   - Exact positioning and interaction between elements in the composition

7. LAYOUT-SPECIFIC REQUIREMENTS:
{get_layout_specific_requirements(layout)}

8. AVOID COMPLETELY:
   - Any text, numbers, or labels within the image
   - Cluttered or busy compositions
   - Amateur photography quality
   - Inappropriate or casual imagery
   - Competing focal points
   - Dark, gloomy, or unprofessional tones
   - Copyright-protected logos or brands
   - Low resolution or pixelated elements

FINAL OUTPUT:
Generate an extremely comprehensive, highly detailed image description (300-1000 characters) that incorporates all the above requirements and directly relates to the specific slide content provided. The description should be suitable for professional AI image generation and result in a high-quality PowerPoint slide image.

Focus on creating imagery that not only looks professional but genuinely enhances and supports the specific content written on this slide. Be extremely specific about:
- Exact objects and their placement in the scene
- Detailed lighting conditions and shadows
- Precise composition and camera angle
- Specific colors, textures, and materials
- Detailed descriptions of people (if included) including their expressions, clothing, and actions
- Environmental details that create atmosphere and context
- Visual metaphors and symbolic elements that reinforce the message

RESPONSE FORMAT: Provide ONLY the highly detailed image description text, nothing else. Aim for 300-1000 characters of rich, specific visual detail that will create a compelling and professional image."""

    return detailed_prompt

def format_slide_content_for_prompt(slide_content, layout):
    """Format slide content into readable text for image prompt context"""
    
    formatted_content = []
    
    if layout == "titleAndBullets":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        bullets = slide_content.get('bullets', [])
        if bullets:
            formatted_content.append("BULLET POINTS:")
            for i, bullet in enumerate(bullets, 1):
                formatted_content.append(f"  {i}. {bullet}")
    
    elif layout == "quote":
        formatted_content.append(f"QUOTE: \"{slide_content.get('quote', '')}\"")
        formatted_content.append(f"AUTHOR: {slide_content.get('author', '')}")
    
    elif layout == "imageAndParagraph":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        formatted_content.append(f"MAIN PARAGRAPH: {slide_content.get('paragraph', '')}")
        current_img_desc = slide_content.get('imageDescription', '')
        if current_img_desc and current_img_desc not in ['Image', 'Image placeholder']:
            formatted_content.append(f"CURRENT IMAGE CONCEPT: {current_img_desc}")
    
    elif layout == "twoColumn":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        formatted_content.append(f"LEFT COLUMN - {slide_content.get('column1Title', '')}: {slide_content.get('column1Content', '')}")
        formatted_content.append(f"RIGHT COLUMN - {slide_content.get('column2Title', '')}: {slide_content.get('column2Content', '')}")
    
    elif layout == "imageWithFeatures":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        features = slide_content.get('features', [])
        if features:
            formatted_content.append("KEY FEATURES:")
            for i, feature in enumerate(features, 1):
                formatted_content.append(f"  {i}. {feature.get('title', '')}: {feature.get('description', '')}")
    
    elif layout == "numberedFeatures":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        features = slide_content.get('features', [])
        if features:
            formatted_content.append("NUMBERED FEATURES:")
            for feature in features:
                num = feature.get('number', '')
                title = feature.get('title', '')
                desc = feature.get('description', '')
                formatted_content.append(f"  {num}. {title}: {desc}")
    
    elif layout == "benefitsGrid":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        benefits = slide_content.get('benefits', [])
        if benefits:
            formatted_content.append("KEY BENEFITS:")
            for i, benefit in enumerate(benefits, 1):
                formatted_content.append(f"  {i}. {benefit.get('title', '')}: {benefit.get('description', '')}")
    
    elif layout == "iconGrid":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        categories = slide_content.get('categories', [])
        if categories:
            formatted_content.append("TARGET CATEGORIES:")
            for i, category in enumerate(categories, 1):
                formatted_content.append(f"  {i}. {category.get('name', '')}: {category.get('description', '')}")
    
    elif layout == "sideBySideComparison":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        formatted_content.append(f"LEFT SIDE - {slide_content.get('leftTitle', '')}:")
        left_points = slide_content.get('leftPoints', [])
        for point in left_points:
            formatted_content.append(f"  • {point}")
        formatted_content.append(f"RIGHT SIDE - {slide_content.get('rightTitle', '')}:")
        right_points = slide_content.get('rightPoints', [])
        for point in right_points:
            formatted_content.append(f"  • {point}")
    
    elif layout == "timeline":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        events = slide_content.get('events', [])
        if events:
            formatted_content.append("TIMELINE EVENTS:")
            for event in events:
                year = event.get('year', '')
                title = event.get('title', '')
                desc = event.get('description', '')
                formatted_content.append(f"  {year}: {title} - {desc}")
    
    elif layout == "conclusion":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        formatted_content.append(f"SUMMARY: {slide_content.get('summary', '')}")
        next_steps = slide_content.get('nextSteps', [])
        if next_steps:
            formatted_content.append("NEXT STEPS:")
            for i, step in enumerate(next_steps, 1):
                formatted_content.append(f"  {i}. {step}")
    
    elif layout == "titleOnly":
        formatted_content.append(f"TITLE: {slide_content.get('title', '')}")
        formatted_content.append(f"SUBTITLE: {slide_content.get('subtitle', '')}")
    
    return "\n".join(formatted_content)

def get_layout_specific_requirements(layout):
    """Get specific visual requirements for each layout type"""
    
    requirements = {
        "imageAndParagraph": """
   - Main subject positioned left or center-left for text space on right
   - Single, clear focal point that represents the paragraph content
   - Professional product photography or conceptual illustration style
   - Clean background with subtle texture or gradient
   - Appropriate depth of field with sharp focus on main subject""",

        "imageWithFeatures": """
   - Central product or concept visualization 
   - 4 distinct areas subtly indicated for feature callouts (without numbers/text)
   - Technical demonstration or cutaway view style
   - Multiple angles or perspectives showing different aspects
   - Clean, studio-lit product photography aesthetic""",


        "numberedFeatures": """
   - 4 distinct sections or areas in the composition (2x2 grid or linear progression)
   - Sequential flow indicators (arrows, pathways, connections)
   - Process visualization or step-by-step demonstration
   - Each section should have unique visual character while maintaining unity
   - Clear spatial organization for number overlay placement"""


    }
    
    return requirements.get(layout, "- Standard professional imagery appropriate for business presentations")

def validate_character_limits(content, layout):
    """Validate that generated content meets character limits"""
    
    LIMITS = {
        'titleOnly': {'title': 60, 'subtitle': 120},
        'titleAndBullets': {'title': 80, 'bullets': 150},
        'quote': {'quote': 200, 'author': 50},
        'imageAndParagraph': {'title': 80, 'paragraph': 300, 'imageDescription': 100},
        'twoColumn': {'title': 80, 'column1Title': 60, 'column2Title': 60, 'column1Content': 300, 'column2Content': 300},
        'imageWithFeatures': {'title': 80, 'imageDescription': 80, 'feature_title': 40, 'feature_description': 50},
        'numberedFeatures': {'title': 80, 'imageDescription': 80, 'feature_title': 40, 'feature_description': 100},
        'benefitsGrid': {'title': 60, 'imageDescription': 80, 'benefit_title': 30, 'benefit_description': 60},
        'iconGrid': {'title': 60, 'category_name': 25, 'category_description': 40},
        'sideBySideComparison': {'title': 80, 'leftTitle': 40, 'rightTitle': 40, 'point': 120},
        'timeline': {'title': 60, 'event_title': 40, 'event_description': 100},
        'conclusion': {'title': 60, 'summary': 100, 'next_step': 50
        },
    }
    
    limits = LIMITS.get(layout, {})
    violations = []
    
    for field, limit in limits.items():
        if field in content:
            if field == 'bullets' and isinstance(content[field], list):
                for i, bullet in enumerate(content[field]):
                    if len(str(bullet)) > limit:
                        violations.append(f"Bullet {i+1}: {len(str(bullet))} > {limit} chars")
            elif field == 'features' and isinstance(content[field], list):
                for i, feature in enumerate(content[field]):
                    if isinstance(feature, dict):
                        if 'title' in feature and len(str(feature['title'])) > limits.get('feature_title', 40):
                            violations.append(f"Feature {i+1} title: {len(str(feature['title']))} > {limits.get('feature_title', 40)} chars")
                        if 'description' in feature and len(str(feature['description'])) > limits.get('feature_description', 100):
                            violations.append(f"Feature {i+1} description: {len(str(feature['description']))} > {limits.get('feature_description', 100)} chars")
            elif field == 'benefits' and isinstance(content[field], list):
                for i, benefit in enumerate(content[field]):
                    if isinstance(benefit, dict):
                        if 'title' in benefit and len(str(benefit['title'])) > limits.get('benefit_title', 30):
                            violations.append(f"Benefit {i+1} title: {len(str(benefit['title']))} > {limits.get('benefit_title', 30)} chars")
                        if 'description' in benefit and len(str(benefit['description'])) > limits.get('benefit_description', 60):
                            violations.append(f"Benefit {i+1} description: {len(str(benefit['description']))} > {limits.get('benefit_description', 60)} chars")
            elif field == 'categories' and isinstance(content[field], list):
                for i, category in enumerate(content[field]):
                    if isinstance(category, dict):
                        if 'name' in category and len(str(category['name'])) > limits.get('category_name', 25):
                            violations.append(f"Category {i+1} name: {len(str(category['name']))} > {limits.get('category_name', 25)} chars")
                        if 'description' in category and len(str(category['description'])) > limits.get('category_description', 0):
                            violations.append(f"Category {i+1} description: {len(str(category['description']))} > {limits.get('category_description', 70)} chars")
            elif field == 'events' and isinstance(content[field], list):
                for i, event in enumerate(content[field]):
                    if isinstance(event, dict):
                        if 'title' in event and len(str(event['title'])) > limits.get('event_title', 40):
                            violations.append(f"Event {i+1} title: {len(str(event['title']))} > {limits.get('event_title', 40)} chars")
                        if 'description' in event and len(str(event['description'])) > limits.get('event_description', 100):
                            violations.append(f"Event {i+1} description: {len(str(event['description']))} > {limits.get('event_description', 100)} chars")
            elif field in ['leftPoints', 'rightPoints'] and isinstance(content[field], list):
                for i, point in enumerate(content[field]):
                    if len(str(point)) > limits.get('point', 120):
                        violations.append(f"{field} {i+1}: {len(str(point))} > {limits.get('point', 120)} chars")
            elif field == 'nextSteps' and isinstance(content[field], list):
                for i, step in enumerate(content[field]):
                    if len(str(step)) > limits.get('next_step', 50):
                        violations.append(f"Next step {i+1}: {len(str(step))} > {limits.get('next_step', 50)} chars")
            elif len(str(content[field])) > limit:
                violations.append(f"{field}: {len(str(content[field]))} > {limit} chars")
    
    return violations

def validate_and_fix_icon_grid(content_result, topic):
    """Validates that an iconGrid layout has exactly 8 categories"""
    logger.debug("Validating and fixing iconGrid content")
    
    if not isinstance(content_result, dict):
        logger.warning("Content result is not a dictionary, creating new one")
        content_result = {}
    
    if 'title' not in content_result or not content_result['title']:
        logger.debug("Adding default title")
        content_result['title'] = f"Impact Areas for {topic.capitalize()}"
    
    if 'categories' not in content_result:
        logger.warning("No categories found, creating empty list")
        content_result['categories'] = []
    
    default_categories = [
        {"name": "Workplace", "description": "Employment and career opportunities"},
        {"name": "Education", "description": "Academic and learning environments"},
        {"name": "Healthcare", "description": "Medical treatment and research"},
        {"name": "Technology", "description": "STEM fields and innovation"},
        {"name": "Politics", "description": "Government and public service"},
        {"name": "Sports", "description": "Athletics and competition"},
        {"name": "Finance", "description": "Banking and investment"},
        {"name": "Media", "description": "Representation and coverage"}
    ]
    
    categories = content_result['categories']
    
    logger.debug(f"Current categories count: {len(categories)}")
    
    if len(categories) < 8:
        logger.info(f"Adding {8 - len(categories)} more categories")
        
        for i in range(len(categories), 8):
            existing_names = [cat.get('name', '').lower() for cat in categories]
            
            suitable_category = None
            for default_cat in default_categories:
                if default_cat['name'].lower() not in existing_names:
                    suitable_category = default_cat.copy()
                    break
            
            if not suitable_category:
                suitable_category = {
                    "name": f"Area {i+1}",
                    "description": f"Impact area {i+1}"
                }
            
            categories.append(suitable_category)
            logger.debug(f"Added category: {suitable_category['name']}")
    
    elif len(categories) > 8:
        logger.info(f"Trimming down to 8 categories (removing {len(categories) - 8})")
        categories = categories[:8]
    
    for i, category in enumerate(categories):
        if not isinstance(category, dict):
            logger.warning(f"Category {i} is not a dictionary, replacing with default")
            categories[i] = default_categories[i % len(default_categories)].copy()
            category = categories[i]
        
        if 'name' not in category or not category['name']:
            logger.debug(f"Category {i} missing name, adding default")
            category['name'] = default_categories[i % len(default_categories)]['name']
        
        if 'description' not in category or not category['description']:
            logger.debug(f"Category {i} missing description, adding default")
            category['description'] = default_categories[i % len(default_categories)]['description']
    
    content_result['categories'] = categories
    logger.debug(f"Final categories count: {len(categories)}")
    
    return content_result

def validate_and_fix_numbered_features(content_result, topic):
    """Validates and fixes numberedFeatures content to ensure correct structure"""
    logger.debug("Validating and fixing numberedFeatures content")
    
    if not isinstance(content_result, dict):
        logger.warning("Content result is not a dictionary, creating new one")
        content_result = {}
    
    if 'title' not in content_result or not content_result['title']:
        logger.debug("Adding default title")
        content_result['title'] = f"Key Points about {topic.capitalize()}"
    
    if 'features' not in content_result:
        logger.warning("No features found, creating empty list")
        content_result['features'] = []
    
    default_features = [
        {"number": "1", "title": "First Key Point", "description": "Description of the first key point"},
        {"number": "2", "title": "Second Key Point", "description": "Description of the second key point"},
        {"number": "3", "title": "Third Key Point", "description": "Description of the third key point"},
        {"number": "4", "title": "Fourth Key Point", "description": "Description of the fourth key point"}
    ]
    
    features = content_result['features']
    
    if not isinstance(features, list):
        logger.warning("Features is not a list, replacing with default features")
        features = default_features.copy()
    
    logger.debug(f"Current features count: {len(features)}")
    
    # Ensure exactly 4 features
    if len(features) < 4:
        logger.info(f"Adding {4 - len(features)} more features")
        for i in range(len(features), 4):
            features.append(default_features[i].copy())
    elif len(features) > 4:
        logger.info(f"Trimming down to 4 features (removing {len(features) - 4})")
        features = features[:4]
    
    # Validate and fix each feature's structure
    for i, feature in enumerate(features):
        if not isinstance(feature, dict):
            logger.warning(f"Feature {i} is not a dictionary, replacing with default")
            features[i] = default_features[i].copy()
            continue
            
        # Ensure number field exists and is correct
        feature['number'] = str(i + 1)
        
        # Ensure title exists and has content
        if 'title' not in feature or not feature['title']:
            logger.debug(f"Feature {i} missing title, adding default")
            feature['title'] = default_features[i]['title']
        
        # Ensure description exists and has content    
        if 'description' not in feature or not feature['description']:
            logger.debug(f"Feature {i} missing description, adding default")
            feature['description'] = default_features[i]['description']
    
    content_result['features'] = features
    logger.debug(f"Final features count: {len(features)}")
    
    return content_result


def process_full_document_for_presentation(full_text, topic, processing_mode='preserve'):
    """
    Stage 1: Analyze the full document and create a presentation plan using native JSON
    """
    
    mode_config = PROCESSING_MODES.get(processing_mode, PROCESSING_MODES['preserve'])
    
    # Limit text to prevent token overflow (keep first and last parts for context)
    if len(full_text) > 4000:
        document_sample = full_text[:2000] + "\n\n[... CONTENT CONTINUES ...]\n\n" + full_text[-2000:]
    else:
        document_sample = full_text
    
    analysis_prompt = f"""You are an expert presentation designer. Analyze this document and create an optimal presentation structure.

DOCUMENT CONTENT:
{document_sample}

TOPIC: {topic}
PROCESSING MODE: {processing_mode}

MODE INSTRUCTION: {mode_config['instruction']}

Analyze the document and determine:
1. Main themes and key sections
2. Optimal number of slides (3-8 recommended)
3. Best slide structure for this content
4. Content focus for each slide

Required JSON format:
{{
    "document_analysis": {{
        "main_themes": ["theme1", "theme2", "theme3"],
        "key_sections": ["introduction", "main_content", "conclusion"],
        "document_type": "report",
        "complexity_level": "medium"
    }},
    "presentation_plan": {{
        "recommended_slides": 5,
        "reasoning": "5 slides work well for this content length and complexity",
        "slide_structure": [
            {{
                "slide_number": 1,
                "layout": "titleOnly",
                "purpose": "Introduction",
                "content_focus": "Document title and overview",
                "source_section": "beginning"
            }},
            {{
                "slide_number": 2,
                "layout": "titleAndBullets",
                "purpose": "Main points",
                "content_focus": "Key findings from document",
                "source_section": "section1"
            }},
            {{
                "slide_number": 3,
                "layout": "imageAndParagraph",
                "purpose": "Detailed explanation",
                "content_focus": "Core concept analysis",
                "source_section": "section2"
            }},
            {{
                "slide_number": 4,
                "layout": "twoColumn",
                "purpose": "Comparison or analysis",
                "content_focus": "Comparative information",
                "source_section": "section3"
            }},
            {{
                "slide_number": 5,
                "layout": "conclusion",
                "purpose": "Summary and next steps",
                "content_focus": "Key takeaways and actions",
                "source_section": "conclusion"
            }}
        ]
    }}
}}

Focus on creating a logical flow that effectively communicates the document's core message."""

    try:
        logger.info(f"Starting document analysis in {processing_mode} mode")
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": analysis_prompt,
                "stream": False,
                "format": "json",  # Enable native JSON mode
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.8,
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            try:
                # Parse JSON directly
                analysis_result = json.loads(generated_text)
                
                # Validate the analysis structure
                if validate_document_analysis(analysis_result):
                    logger.info(f"✅ Successfully analyzed document: {analysis_result['presentation_plan']['recommended_slides']} slides planned")
                    return {{
                        'success': True,
                        'analysis': analysis_result,
                        'full_text': full_text,
                        'processing_mode': processing_mode
                    }}
                else:
                    logger.warning("⚠️ Document analysis validation failed")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON decode error in document analysis: {e}")
                logger.debug(f"Raw analysis response: {generated_text[:300]}...")
                
        else:
            logger.error(f"❌ Ollama API error in document analysis: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Exception in document analysis: {e}")
    
    # Fallback analysis
    logger.info("🔄 Using fallback document analysis")
    return create_fallback_document_analysis(full_text, topic, processing_mode)


def create_fallback_document_analysis(full_text, topic, processing_mode):
    """
    Enhanced fallback analysis when Ollama analysis fails
    """
    
    word_count = len(full_text.split())
    
    # Determine slide count based on content length
    if word_count < 200:
        slide_count = 3
    elif word_count < 600:
        slide_count = 4
    elif word_count < 1200:
        slide_count = 5
    elif word_count < 2000:
        slide_count = 6
    else:
        slide_count = min(8, max(6, word_count // 300))
    
    # Analyze text for themes (simple keyword extraction)
    text_lower = full_text.lower()
    common_themes = []
    
    # Look for common document themes
    theme_keywords = {
        'analysis': ['analysis', 'analyze', 'study', 'research', 'findings'],
        'strategy': ['strategy', 'plan', 'approach', 'method', 'implementation'],
        'results': ['results', 'outcomes', 'performance', 'metrics', 'data'],
        'recommendations': ['recommend', 'suggest', 'propose', 'should', 'next steps'],
        'challenges': ['challenge', 'problem', 'issue', 'difficulty', 'obstacle'],
        'opportunities': ['opportunity', 'potential', 'benefit', 'advantage', 'growth']
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            common_themes.append(theme.capitalize())
    
    if not common_themes:
        common_themes = [topic, 'Key Points', 'Analysis']
    
    # Create basic structure
    slide_structure = []
    
    # Title slide
    slide_structure.append({
        "slide_number": 1,
        "layout": "titleOnly",
        "purpose": "Introduction",
        "content_focus": f"Title and overview of {topic}",
        "source_section": "beginning"
    })
    
    # Content slides with varied layouts
    available_layouts = ["titleAndBullets", "imageAndParagraph", "twoColumn", "quote"]
    content_slides_needed = slide_count - 2  # Exclude title and conclusion
    
    for i in range(content_slides_needed):
        slide_number = i + 2
        layout = available_layouts[i % len(available_layouts)]
        
        slide_structure.append({
            "slide_number": slide_number,
            "layout": layout,
            "purpose": f"Content section {i + 1}",
            "content_focus": f"Key points from section {i + 1}",
            "source_section": f"section{i + 1}"
        })
    
    # Conclusion slide
    slide_structure.append({
        "slide_number": slide_count,
        "layout": "conclusion",
        "purpose": "Summary and next steps",
        "content_focus": "Key takeaways and recommendations",
        "source_section": "conclusion"
    })
    
    logger.info(f"📋 Created fallback analysis: {slide_count} slides with themes: {', '.join(common_themes[:3])}")
    
    return {
        'success': False,
        'analysis': {
            'document_analysis': {
                'main_themes': common_themes[:3],
                'key_sections': ["Introduction", "Main Content", "Analysis", "Conclusion"],
                'document_type': 'document',
                'complexity_level': 'medium' if word_count > 1000 else 'low'
            },
            'presentation_plan': {
                'recommended_slides': slide_count,
                'reasoning': f'Fallback structure based on {word_count} words and detected themes',
                'slide_structure': slide_structure
            }
        },
        'full_text': full_text,
        'processing_mode': processing_mode
    }


def validate_slide_content_enhanced(content, layout, slide_plan):
    """
    Enhanced validation with proper type checking to prevent unhashable dict errors
    """
    # DEBUG: Log the types and values to identify the issue
    logger.debug(f"=== VALIDATION DEBUG ===")
    logger.debug(f"content type: {type(content)}")
    logger.debug(f"layout type: {type(layout)}, value: {layout}")
    logger.debug(f"slide_plan type: {type(slide_plan)}")
    
    # FIX: Ensure layout is always a string
    if isinstance(layout, dict):
        logger.error(f"❌ Layout is a dictionary instead of string: {layout}")
        # Extract layout from dictionary if it's nested
        if 'layout' in layout:
            layout = layout['layout']
            logger.info(f"✅ Extracted layout string: {layout}")
        else:
            logger.error(f"❌ Cannot extract layout string from dict: {layout}")
            return False
    
    if not isinstance(layout, str):
        logger.error(f"❌ Layout is not a string: {type(layout)} - {layout}")
        return False
    
    if not isinstance(content, dict):
        logger.debug(f"Content is not a dict for {layout}")
        return False
    
    # Check for required fields based on layout
    try:
        schema = get_layout_json_schema(layout)
        required_fields = schema.get('required', [])
        
        logger.debug(f"Schema for {layout}: required fields = {required_fields}")
        
        for field in required_fields:
            if field not in content:
                logger.debug(f"Missing required field '{field}' for {layout}")
                return False
            
            if not content[field]:
                logger.debug(f"Empty required field '{field}' for {layout}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error getting schema for layout '{layout}': {e}")
        return False
    
    # Check for generic/placeholder content
    generic_patterns = [
        'placeholder', 'example content', 'lorem ipsum', 'insert here',
        'content goes here', 'sample text', 'description of', 'explanation of',
        'content for', 'text for', 'information about', 'details about'
    ]
    
    content_str = str(content).lower()
    for pattern in generic_patterns:
        if pattern in content_str:
            logger.debug(f"Generic pattern '{pattern}' found in {layout}")
            return False
    
    # Layout-specific validation
    if layout == 'titleAndBullets':
        bullets = content.get('bullets', [])
        if len(bullets) < 3:
            logger.debug(f"Too few bullets ({len(bullets)}) for titleAndBullets")
            return False
        
        # Check bullet quality
        for bullet in bullets[:3]:
            if len(str(bullet)) < 15:
                logger.debug(f"Bullet too short: {bullet}")
                return False
    
    elif layout == 'imageAndParagraph':
        paragraph = content.get('paragraph', '')
        if len(paragraph) < 50:
            logger.debug(f"Paragraph too short ({len(paragraph)}) for imageAndParagraph")
            return False
    
    elif layout == 'conclusion':
        next_steps = content.get('nextSteps', [])
        if len(next_steps) < 2:
            logger.debug(f"Too few next steps ({len(next_steps)}) for conclusion")
            return False
    
    logger.debug(f"✅ Validation passed for {layout}")
    return True


def validate_document_analysis(analysis_result):
    """
    Validate the document analysis structure with proper error handling
    """
    logger.debug(f"=== DOCUMENT ANALYSIS VALIDATION DEBUG ===")
    logger.debug(f"analysis_result type: {type(analysis_result)}")
    
    try:
        # Check top-level structure
        if not isinstance(analysis_result, dict):
            logger.debug(f"Analysis result is not a dict: {type(analysis_result)}")
            return False
        
        required_top_keys = ['document_analysis', 'presentation_plan']
        for key in required_top_keys:
            if key not in analysis_result:
                logger.debug(f"Missing top-level key: {key}")
                return False
        
        # Check document_analysis section
        doc_analysis = analysis_result['document_analysis']
        if not isinstance(doc_analysis, dict):
            logger.debug(f"document_analysis is not a dict: {type(doc_analysis)}")
            return False
            
        required_doc_keys = ['main_themes', 'key_sections', 'document_type', 'complexity_level']
        for key in required_doc_keys:
            if key not in doc_analysis:
                logger.debug(f"Missing document_analysis key: {key}")
                return False
        
        # Check presentation_plan section
        pres_plan = analysis_result['presentation_plan']
        if not isinstance(pres_plan, dict):
            logger.debug(f"presentation_plan is not a dict: {type(pres_plan)}")
            return False
            
        required_plan_keys = ['recommended_slides', 'reasoning', 'slide_structure']
        for key in required_plan_keys:
            if key not in pres_plan:
                logger.debug(f"Missing presentation_plan key: {key}")
                return False
        
        # Validate slide structure
        slide_structure = pres_plan['slide_structure']
        if not isinstance(slide_structure, list):
            logger.debug(f"slide_structure is not a list: {type(slide_structure)}")
            return False
            
        if len(slide_structure) < 3:
            logger.debug(f"Too few slides in structure: {len(slide_structure)}")
            return False
        
        # Check each slide in structure
        required_slide_keys = ['slide_number', 'layout', 'purpose', 'content_focus', 'source_section']
        for i, slide in enumerate(slide_structure):
            logger.debug(f"Validating slide {i}: {type(slide)}")
            
            if not isinstance(slide, dict):
                logger.debug(f"Slide {i} is not a dict: {type(slide)}")
                return False
            
            for key in required_slide_keys:
                if key not in slide:
                    logger.debug(f"Slide {i} missing key: {key}")
                    return False
                    
                # Ensure layout is a string
                if key == 'layout' and not isinstance(slide[key], str):
                    logger.debug(f"Slide {i} layout is not a string: {type(slide[key])} - {slide[key]}")
                    return False
        
        # Check slide count consistency
        recommended_slides = pres_plan['recommended_slides']
        actual_slides = len(slide_structure)
        if recommended_slides != actual_slides:
            logger.debug(f"Slide count mismatch: recommended {recommended_slides}, actual {actual_slides}")
            # Don't fail for count mismatch, just log it
            logger.warning(f"⚠️ Slide count mismatch but continuing: recommended {recommended_slides}, actual {actual_slides}")
        
        logger.debug("✅ Document analysis validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Document analysis validation error: {e}")
        import traceback
        logger.error(f"Validation traceback: {traceback.format_exc()}")
        return False


def generate_slide_with_retry(slide_plan, full_document, document_analysis, processing_mode, max_retries=3):
    """
    Generate slide with retry mechanism - FIXED to prevent dict/string confusion
    """
    # DEBUG: Log slide_plan structure
    logger.debug(f"=== SLIDE GENERATION DEBUG ===")
    logger.debug(f"slide_plan type: {type(slide_plan)}")
    logger.debug(f"slide_plan content: {slide_plan}")
    
    # FIX: Ensure we extract layout as string, not dict
    if isinstance(slide_plan, dict):
        layout = slide_plan.get('layout', 'titleAndBullets')
        slide_number = slide_plan.get('slide_number', 1)
    else:
        logger.error(f"❌ slide_plan is not a dict: {type(slide_plan)}")
        layout = 'titleAndBullets'
        slide_number = 1
    
    # ENSURE layout is always a string
    if not isinstance(layout, str):
        logger.error(f"❌ Layout extracted is not a string: {type(layout)} - {layout}")
        layout = 'titleAndBullets'  # Safe fallback
    
    logger.debug(f"✅ Layout confirmed as string: '{layout}'")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Generating slide {slide_number} ({layout}) - Attempt {attempt + 1}/{max_retries}")
            
            # Extract relevant text section
            relevant_text = extract_document_section(
                full_document, 
                slide_plan.get('source_section', ''), 
                slide_number, 
                len(document_analysis['presentation_plan']['slide_structure'])
            )
            
            # Create the prompt
            prompt = create_document_slide_prompt_json(
                layout=layout,  # This is now guaranteed to be a string
                relevant_text=relevant_text,
                content_focus=slide_plan.get('content_focus', ''),
                purpose=slide_plan.get('purpose', ''),
                processing_mode=processing_mode,
                document_context=document_analysis.get('document_analysis', {}),
                attempt_number=attempt + 1
            )
            
            # Get JSON schema for the layout
            json_schema = get_layout_json_schema(layout)  # layout is guaranteed string
            
            mode_config = PROCESSING_MODES.get(processing_mode, PROCESSING_MODES['preserve'])
            
            # Call Ollama with native JSON format
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Enable native JSON mode
                    "options": {
                        "temperature": mode_config['temperature'] + (attempt * 0.1),  # Slightly increase creativity on retries
                        "top_p": mode_config['top_p'],
                        "repeat_penalty": 1.1
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_content = result.get("response", "")
                
                try:
                    # Parse the JSON response directly
                    content_result = json.loads(generated_content)
                    
                    # Validate the content - PASS layout as string and slide_plan as dict
                    if validate_slide_content_enhanced(content_result, layout, slide_plan):
                        logger.info(f"✅ Successfully generated slide {slide_number} on attempt {attempt + 1}")
                        return content_result
                    else:
                        logger.warning(f"⚠️ Content validation failed for slide {slide_number}, attempt {attempt + 1}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ JSON decode error for slide {slide_number}, attempt {attempt + 1}: {e}")
                    logger.debug(f"Raw response: {generated_content[:200]}...")
                    
            else:
                logger.error(f"❌ Ollama API error for slide {slide_number}, attempt {attempt + 1}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Exception generating slide {slide_number}, attempt {attempt + 1}: {e}")
            import traceback
            logger.error(f"Generation traceback: {traceback.format_exc()}")
    
    # All retries failed, use fallback
    logger.warning(f"🔄 All retries failed for slide {slide_number}, using intelligent fallback")

def create_document_slide_prompt_json(layout, relevant_text, content_focus, purpose, processing_mode, document_context, attempt_number=1):
    """
    Create prompts optimized for Ollama's native JSON mode
    """
    
    # Limit text to prevent token overflow
    if len(relevant_text) > 1800:
        relevant_text = relevant_text[:1800] + "..."
    
    mode_config = PROCESSING_MODES.get(processing_mode, PROCESSING_MODES['preserve'])
    
    # Add attempt-specific variations to avoid repeated failures
    attempt_variation = ""
    if attempt_number > 1:
        attempt_variation = f"\n\nATTEMPT {attempt_number}: Please ensure all JSON fields are properly filled with meaningful content. Avoid generic placeholders."
    
    base_context = f"""You are an expert presentation designer creating slides from document content.

PROCESSING MODE: {processing_mode.upper()}
INSTRUCTION: {mode_config['instruction']}

DOCUMENT SECTION:
{relevant_text}

SLIDE DETAILS:
- Purpose: {purpose}
- Content Focus: {content_focus}
- Document Type: {document_context.get('document_type', 'document')}
- Main Themes: {', '.join(document_context.get('main_themes', [])[:3])}

{attempt_variation}

You must return ONLY valid JSON matching the exact schema provided. Do not include any explanations or markdown formatting."""

    layout_prompts = {
        'titleOnly': f"""{base_context}

Create a compelling title slide from the document content.

Required JSON format:
{{
    "title": "Engaging main title from document (max 60 chars)",
    "subtitle": "Descriptive subtitle that previews content (max 120 chars)"
}}

Extract or create a powerful title that represents the document's main message.""",

        'titleAndBullets': f"""{base_context}

Extract key points from the document section as bullet points.

Required JSON format:
{{
    "title": "Clear section title (max 80 chars)",
    "bullets": [
        "First key point (max 150 chars)",
        "Second key point (max 150 chars)",
        "Third key point (max 150 chars)",
        "Fourth key point (max 150 chars)"
    ]
}}

Create 3-5 specific, actionable bullet points from the document content.""",

        'imageAndParagraph': f"""{base_context}

Create detailed content with a descriptive paragraph from the document.

Required JSON format:
{{
    "title": "Descriptive title (max 80 chars)",
    "imageDescription": "Detailed image description relevant to content (max 400 chars)",
    "paragraph": "Comprehensive explanation from document (max 400 chars)"
}}

Extract and format the key information into a detailed paragraph.""",

        'conclusion': f"""{base_context}

Create a conclusion slide summarizing the document's key insights.

Required JSON format:
{{
    "title": "Conclusion title (max 60 chars)",
    "summary": "Summary of key insights from document (max 200 chars)",
    "nextSteps": [
        "First actionable step (max 50 chars)",
        "Second actionable step (max 50 chars)",
        "Third actionable step (max 50 chars)"
    ]
}}

Summarize main findings and provide actionable next steps.""",

        'quote': f"""{base_context}

Find the most impactful quote or statement from the document.

Required JSON format:
{{
    "quote": "Powerful quote from document (max 200 chars)",
    "author": "Source or context (max 50 chars)"
}}

Extract a meaningful quote that captures the essence of the content.""",

        'twoColumn': f"""{base_context}

Split the content into two complementary sections.

Required JSON format:
{{
    "title": "Comparison or analysis title (max 80 chars)",
    "column1Title": "First aspect title (max 60 chars)",
    "column1Content": "Content for first aspect (max 300 chars)",
    "column2Title": "Second aspect title (max 60 chars)",
    "column2Content": "Content for second aspect (max 300 chars)"
}}

Divide the information into two related but distinct sections.""",

        'timeline': f"""{base_context}

Create a timeline from chronological information in the document.

Required JSON format:
{{
    "title": "Timeline title (max 60 chars)",
    "events": [
        {{"year": "2020", "title": "Event name (max 40 chars)", "description": "Description (max 100 chars)"}},
        {{"year": "2023", "title": "Event name (max 40 chars)", "description": "Description (max 100 chars)"}},
        {{"year": "2024", "title": "Event name (max 40 chars)", "description": "Description (max 100 chars)"}}
    ]
}}

Extract chronological events or milestones from the document content."""
    }
    
    return layout_prompts.get(layout, f"""{base_context}

Create appropriate {layout} content from the document section.
Return valid JSON only with all required fields properly filled.""")


def get_layout_json_schema(layout):
    """
    Define JSON schemas for each layout to help with validation
    """
    schemas = {
        'titleOnly': {
            "type": "object",
            "properties": {
                "title": {"type": "string", "maxLength": 60},
                "subtitle": {"type": "string", "maxLength": 120}
            },
            "required": ["title", "subtitle"]
        },
        'titleAndBullets': {
            "type": "object", 
            "properties": {
                "title": {"type": "string", "maxLength": 80},
                "bullets": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 150},
                    "minItems": 3,
                    "maxItems": 5
                }
            },
            "required": ["title", "bullets"]
        },
        'imageAndParagraph': {
            "type": "object",
            "properties": {
                "title": {"type": "string", "maxLength": 80},
                "imageDescription": {"type": "string", "maxLength": 400},
                "paragraph": {"type": "string", "maxLength": 400}
            },
            "required": ["title", "imageDescription", "paragraph"]
        },
        'conclusion': {
            "type": "object",
            "properties": {
                "title": {"type": "string", "maxLength": 60},
                "summary": {"type": "string", "maxLength": 200},
                "nextSteps": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 50},
                    "minItems": 2,
                    "maxItems": 4
                }
            },
            "required": ["title", "summary", "nextSteps"]
        }
    }
    
    return schemas.get(layout, {})




def generate_slide_from_document_section(slide_plan, full_document, document_analysis, processing_mode):
    """
    Updated function using retry mechanism
    """
    return generate_slide_with_retry(slide_plan, full_document, document_analysis, processing_mode)

def create_document_slide_prompt(layout, relevant_text, content_focus, purpose, processing_mode, mode_config, document_context):
    """Create specialized prompts for document-based slide generation"""
    
    # Limit relevant text to prevent token overflow
    if len(relevant_text) > 2000:
        relevant_text = relevant_text[:2000] + "..."
    
    base_instruction = f"""
PROCESSING MODE: {processing_mode.upper()}
{mode_config['instruction']}

DOCUMENT SECTION:
{relevant_text}

SLIDE PURPOSE: {purpose}
CONTENT FOCUS: {content_focus}

DOCUMENT CONTEXT:
- Document Type: {document_context.get('document_type', 'document')}
- Main Themes: {', '.join(document_context.get('main_themes', []))}
- Complexity: {document_context.get('complexity_level', 'medium')}
"""

    layout_specific_prompts = {
        'titleOnly': f"""
{base_instruction}

Create a compelling title slide for this presentation.

REQUIREMENTS:
- Extract or create a powerful title that represents the document's main message
- Create an engaging subtitle that previews the key insights
- Follow {processing_mode} mode principles

Return ONLY this JSON:
{{"title": "Compelling presentation title", "subtitle": "Engaging subtitle that previews content"}}
""",

        'titleAndBullets': f"""
{base_instruction}

Extract key points from the document section above.

REQUIREMENTS:
- Create 3-5 bullet points that capture the essential information
- Follow {processing_mode} mode: {'preserve exact wording' if processing_mode == 'preserve' else 'condense key points' if processing_mode == 'condense' else 'enhance and expand key ideas'}
- Make bullets specific and actionable

Return ONLY this JSON:
{{"title": "Section title", "bullets": ["Specific point 1", "Specific point 2", "Specific point 3"]}}
""",

        'imageAndParagraph': f"""
{base_instruction}

Create detailed content from the document section.

REQUIREMENTS:
- Extract or create a comprehensive paragraph that explains the key concept
- Follow {processing_mode} mode principles
- Provide detailed image description relevant to the content

Return ONLY this JSON:
{{"title": "Descriptive title", "imageDescription": "Detailed image description relevant to content", "paragraph": "Comprehensive explanation of the key concept"}}
""",

        'conclusion': f"""
{base_instruction}

Create a conclusion slide that summarizes the document's key insights.

REQUIREMENTS:
- Summarize the main findings from the entire document
- Provide actionable next steps based on the document's recommendations
- Follow {processing_mode} mode principles

Return ONLY this JSON:
{{"title": "Conclusion title", "summary": "Summary of key insights from document", "nextSteps": ["Actionable step 1", "Actionable step 2", "Actionable step 3"]}}
""",

        'quote': f"""
{base_instruction}

Find the most impactful quote or statement from the document section.

REQUIREMENTS:
- Extract a powerful, meaningful quote from the document
- If no direct quote exists, create one that captures the essence
- Provide proper attribution or context

Return ONLY this JSON:
{{"quote": "Powerful quote from or inspired by the document", "author": "Source or context"}}
""",

        'twoColumn': f"""
{base_instruction}

Split the content into two complementary aspects.

REQUIREMENTS:
- Divide the information into two related but distinct sections
- Follow {processing_mode} mode principles
- Create logical comparison or complementary information

Return ONLY this JSON:
{{"title": "Comparison or analysis title", "column1Title": "First aspect", "column1Content": "Content for first aspect", "column2Title": "Second aspect", "column2Content": "Content for second aspect"}}
"""
    }
    
    return layout_specific_prompts.get(layout, f"""
{base_instruction}

Create appropriate {layout} content from the document section above.
Follow {processing_mode} mode principles and return valid JSON only.
""")


def extract_document_section(full_document, source_section, slide_number, total_slides):
    """Extract relevant section from full document based on slide plan"""
    
    if not full_document:
        return ""
    
    # Handle special sections
    if source_section == "beginning":
        return full_document[:1000]
    elif source_section == "end" or source_section == "conclusion":
        return full_document[-1000:]
    elif source_section == "full":
        return full_document
    
    # For regular sections, divide document into parts
    if total_slides <= 3:
        # For short presentations, use larger sections
        if slide_number == 1:
            return full_document[:1500]
        elif slide_number == total_slides:
            return full_document[-1000:]
        else:
            mid_point = len(full_document) // 2
            return full_document[mid_point-500:mid_point+500]
    else:
        # For longer presentations, divide more evenly
        content_slides = total_slides - 2  # Exclude title and conclusion
        if slide_number == 1:  # Title slide
            return full_document[:800]
        elif slide_number == total_slides:  # Conclusion slide
            return full_document[-1000:]
        else:
            # Content slides
            section_index = slide_number - 2
            section_size = len(full_document) // content_slides
            start_pos = section_index * section_size
            end_pos = min(len(full_document), start_pos + section_size + 500)  # Add overlap
            return full_document[start_pos:end_pos]



# Add to ollama_client.py

def generate_presentation_outline(topic, slide_count, input_method='topic', text_content=None):
    """Generate a comprehensive presentation outline"""
    
    logger.info(f"🎯 Generating outline for '{topic}' with {slide_count} slides")
    
    if input_method == 'topic':
        content_context = f"Topic: {topic}"
    elif input_method == 'text' and text_content:
        # Limit text for outline generation
        limited_text = text_content[:1500] if len(text_content) > 1500 else text_content
        content_context = f"Topic: {topic}\n\nSource Content:\n{limited_text}"
    else:
        content_context = f"Topic: {topic}"
    
    outline_prompt = f"""You are an expert presentation designer. Create a comprehensive outline for a {slide_count}-slide presentation.

{content_context}

Create a logical, flowing presentation structure with clear transitions between slides.

Return ONLY this JSON structure:
{{
    "presentation_meta": {{
        "title": "Engaging presentation title",
        "objective": "What this presentation achieves",
        "target_audience": "Who this is for", 
        "key_message": "Main takeaway"
    }},
    "slide_structure": [
        {{
            "slide_number": 1,
            "layout": "titleOnly",
            "title": "Compelling slide title",
            "purpose": "Introduction and hook",
            "key_points": ["Opening hook", "Preview of content"],
            "context": "Sets the stage for the entire presentation",
            "transitions": {{
                "from_previous": null,
                "to_next": "Transitions into main concepts"
            }}
        }},
        {{
            "slide_number": 2,
            "layout": "titleAndBullets",
            "title": "Framework/Overview",
            "purpose": "Establish framework",
            "key_points": ["Key concept 1", "Key concept 2", "Key concept 3"],
            "context": "Builds foundation for detailed exploration",
            "transitions": {{
                "from_previous": "Building on the introduction",
                "to_next": "Each concept will be explored in detail"
            }}
        }}
    ]
}}

LAYOUT GUIDELINES:
- Slide 1: Always "titleOnly" for introduction
- Slide {slide_count}: Always "conclusion" for wrap-up
- Middle slides: Mix of "titleAndBullets", "imageAndParagraph", "twoColumn", "quote", "timeline", etc.
- Ensure logical flow and variety in layouts
- Each slide should have clear purpose and transitions

Create exactly {slide_count} slides with a compelling narrative flow."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": outline_prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2,  # Lower temperature for consistent structure
                    "top_p": 0.8,
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            try:
                outline = json.loads(generated_text)
                
                # Validate outline structure
                if validate_outline_structure(outline, slide_count):
                    logger.info(f"✅ Successfully generated outline with {len(outline['slide_structure'])} slides")
                    return outline
                else:
                    logger.warning("⚠️ Invalid outline structure, using fallback")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON decode error in outline generation: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error generating outline: {e}")
    
    # Fallback outline generation
    logger.info("🔄 Using fallback outline generation")

def validate_outline_structure(outline, expected_slides):
    """Validate the generated outline structure"""
    try:
        # Check required top-level keys
        if not all(key in outline for key in ['presentation_meta', 'slide_structure']):
            return False
        
        # Check presentation meta
        meta = outline['presentation_meta']
        required_meta = ['title', 'objective', 'target_audience', 'key_message']
        if not all(key in meta for key in required_meta):
            return False
        
        # Check slide structure
        slides = outline['slide_structure']
        if len(slides) != expected_slides:
            return False
        
        # Check each slide
        required_slide_keys = ['slide_number', 'layout', 'title', 'purpose', 'key_points', 'context', 'transitions']
        for slide in slides:
            if not all(key in slide for key in required_slide_keys):
                return False
            
            # Check transitions structure
            transitions = slide['transitions']
            if not all(key in transitions for key in ['from_previous', 'to_next']):
                return False
        
        return True
        
    except Exception:
        return False


def generate_slide_with_context(slide_info, full_outline, template_id):
    """Generate individual slide with full presentation context"""
    
    layout = slide_info['layout']
    slide_number = slide_info['slide_number']
    total_slides = len(full_outline['slide_structure'])
    
    # Create context-aware prompt
    presentation_context = f"""
PRESENTATION CONTEXT:
Title: {full_outline['presentation_meta']['title']}
Objective: {full_outline['presentation_meta']['objective']}
Key Message: {full_outline['presentation_meta']['key_message']}

SLIDE POSITION: {slide_number} of {total_slides}

CURRENT SLIDE:
Purpose: {slide_info['purpose']}
Context: {slide_info['context']}
Key Points: {', '.join(slide_info['key_points'])}

FLOW CONTEXT:
Previous Transition: {slide_info['transitions']['from_previous'] or 'Opening slide'}
Next Transition: {slide_info['transitions']['to_next'] or 'Closing slide'}

SURROUNDING SLIDES:
"""
    
    # Add context from previous and next slides
    prev_slide = None
    next_slide = None
    
    for slide in full_outline['slide_structure']:
        if slide['slide_number'] == slide_number - 1:
            prev_slide = slide
        elif slide['slide_number'] == slide_number + 1:
            next_slide = slide
    
    if prev_slide:
        presentation_context += f"Previous Slide: {prev_slide['title']} - {prev_slide['purpose']}\n"
    if next_slide:
        presentation_context += f"Next Slide: {next_slide['title']} - {next_slide['purpose']}\n"
    
    # Generate content with context
    layout_prompts = {
        'titleOnly': f"""
{presentation_context}

Create a compelling title slide that sets the tone for the entire presentation.

Return ONLY this JSON:
{{"title": "Engaging title (max 60 chars)", "subtitle": "Compelling subtitle that previews the journey (max 120 chars)"}}

Title should be: {slide_info['title']}
Make it engaging and set proper expectations for the presentation.
""",

        'titleAndBullets': f"""
{presentation_context}

Create bullet points that advance the presentation narrative and connect to surrounding slides.

Return ONLY this JSON:
{{"title": "Clear section title (max 80 chars)", "bullets": ["Bullet 1 (max 150 chars)", "Bullet 2", "Bullet 3", "Bullet 4"]}}

Title should be: {slide_info['title']}
Create 3-5 bullets that flow logically and connect to the overall presentation arc.
""",

        'imageAndParagraph': f"""
{presentation_context}

Create detailed content that fits naturally in the presentation flow.

Return ONLY this JSON:
{{"title": "Descriptive title (max 80 chars)", "imageDescription": "Detailed image description (max 400 chars)", "paragraph": "Comprehensive explanation (max 400 chars)"}}

Title should be: {slide_info['title']}
Content should build on previous slides and prepare for upcoming content.
""",

        'conclusion': f"""
{presentation_context}

Create a strong conclusion that ties together the entire presentation.

Return ONLY this JSON:
{{"title": "Conclusion title (max 60 chars)", "summary": "Summary that reinforces key message (max 200 chars)", "nextSteps": ["Action 1 (max 50 chars)", "Action 2", "Action 3"]}}

Summarize the journey and provide clear, actionable next steps that align with the presentation objective.
"""
    }
    
    prompt = layout_prompts.get(layout, f"""
{presentation_context}

Create appropriate {layout} content that fits the presentation flow.
Return valid JSON only.
""")
    
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            try:
                content_result = json.loads(generated_text)
                
                # Process content
                content_result['topic'] = full_outline['presentation_meta']['title']
                content_result['slide_index'] = slide_number
                content_result['total_slides'] = total_slides
                
                return process_content_for_layout(content_result, layout)
                
            except json.JSONDecodeError:
                logger.warning(f"JSON decode error for slide {slide_number}")
                
    except Exception as e:
        logger.error(f"Error generating slide {slide_number}: {e}")
    
def generate_slides_from_outline(outline, template_id):
    """Generate all slides using the outline context"""
    
    slides = []
    slide_structure = outline['slide_structure']
    
    logger.info(f"🎨 Generating {len(slide_structure)} slides with context")
    
    for slide_info in slide_structure:
        try:
            content = generate_slide_with_context(slide_info, outline, template_id)
            
            if content:
                slides.append({
                    'layout': slide_info['layout'],
                    'content': content
                })
                logger.info(f"Generated slide {slide_info['slide_number']}: {slide_info['layout']}")
            else:
                logger.warning(f"Failed to generate slide {slide_info['slide_number']}")
                
        except Exception as e:
            logger.error(f"Error generating slide {slide_info['slide_number']}: {e}")
            continue
    
    logger.info(f"✅ Successfully generated {len(slides)} slides with context")
    return slides


def generate_presentation_outline_enhanced(topic, slide_count, input_method='topic', content_context=None, processing_mode='generate'):
    """Enhanced outline generation with content context support"""
    
    logger.info(f"🎯 Generating enhanced outline: method={input_method}, mode={processing_mode}")
    
    # Build context-aware prompt
    if input_method == 'topic':
        content_section = f"Topic: {topic}"
        instruction = "Create a comprehensive presentation outline based on the topic."
        
    elif input_method == 'text' and content_context:
        # Limit content for prompt
        content_preview = content_context['content'][:2000]
        if len(content_context['content']) > 2000:
            content_preview += "..."
            
        content_section = f"""Topic: {topic}

Source Text Content:
{content_preview}

Content Statistics:
- Word Count: {content_context['word_count']}
- Character Count: {content_context['char_count']}"""

        instruction = f"""Analyze the provided text content and create a presentation outline that {
            'preserves the original structure and key points' if processing_mode == 'preserve' else
            'organizes and enhances the content effectively'
        }. Extract the main themes and organize them into a logical flow."""
        
    elif input_method == 'document' and content_context:
        # Limit content for prompt
        content_preview = content_context['content'][:2000]
        if len(content_context['content']) > 2000:
            content_preview += "..."
            
        content_section = f"""Topic: {topic}

Source Document Content:
{content_preview}

Content Statistics:
- Word Count: {content_context['word_count']}
- Character Count: {content_context['char_count']}
- Processing Mode: {processing_mode}"""

        mode_instructions = {
            'preserve': 'maintain the original document structure and wording as much as possible',
            'condense': 'summarize and condense the key points while maintaining the core message',
            'generate': 'enhance and expand the content with additional context and examples'
        }

        instruction = f"""Analyze the provided document content and create a presentation outline that will {mode_instructions.get(processing_mode, 'organize the content effectively')}. Structure the content for maximum impact and clarity."""
    
    else:
        content_section = f"Topic: {topic}"
        instruction = "Create a comprehensive presentation outline."
    
    # Enhanced outline prompt
    outline_prompt = f"""You are an expert presentation designer. {instruction}

{content_section}

Create a detailed presentation outline with exactly {slide_count} slides that tells a compelling story.

REQUIREMENTS:
- Create a logical flow from introduction to conclusion
- Ensure each slide has a clear purpose and connects to the next
- Use varied layouts for visual interest
- Include specific content guidance for each slide
- Add transition guidance between slides

Available layouts: titleOnly, titleAndBullets, imageAndParagraph, twoColumn, quote, timeline, conclusion, imageWithFeatures, numberedFeatures, benefitsGrid, iconGrid, sideBySideComparison

Return ONLY this JSON structure:
{{
    "presentation_meta": {{
        "title": "Engaging presentation title",
        "objective": "What this presentation achieves",
        "target_audience": "Who this is for",
        "key_message": "Main takeaway message"
    }},
    "slide_structure": [
        {{
            "slide_number": 1,
            "layout": "titleOnly",
            "title": "Compelling slide title",
            "purpose": "Introduction and engagement",
            "key_points": ["Opening hook", "Preview of content"],
            "context": "Sets the stage and captures attention",
            "transitions": {{
                "from_previous": null,
                "to_next": "Transitions into main framework"
            }}{
                ', "content_preview": "Brief preview of slide content from source"' if content_context else ''
            }
        }}
    ]
}}

Focus on creating a presentation that flows naturally and engages the audience throughout."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": outline_prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            try:
                outline = json.loads(generated_text)
                
                # Validate and enhance outline
                if validate_outline_structure_enhanced(outline, slide_count):
                    logger.info(f"✅ Enhanced outline generated: {len(outline['slide_structure'])} slides")
                    return outline
                else:
                    logger.warning("⚠️ Enhanced outline validation failed, using fallback")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON decode error in enhanced outline: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error in enhanced outline generation: {e}")
    
    # Fallback outline generation
    logger.info("🔄 Using enhanced fallback outline generation")
    return create_enhanced_fallback_outline(topic, slide_count, input_method, content_context)

def generate_slides_from_outline_enhanced(outline, template_id, content_data=None, processing_mode='preserve'):
    """Enhanced slide generation from outline with content context"""
    
    slides = []
    slide_structure = outline['slide_structure']
    generation_metadata = outline.get('generation_metadata', {})
    input_method = generation_metadata.get('input_method', 'topic')
    
    logger.info(f"🎨 Generating {len(slide_structure)} slides with enhanced context (method: {input_method})")
    
    for slide_info in slide_structure:
        try:
            # Generate slide with enhanced context
            content = generate_slide_with_enhanced_context(
                slide_info=slide_info,
                full_outline=outline,
                template_id=template_id,
                content_data=content_data,
                processing_mode=processing_mode,
                input_method=input_method
            )
            
            if content:
                slides.append({
                    'layout': slide_info['layout'],
                    'content': content
                })
                logger.info(f"Generated slide {slide_info['slide_number']}: {slide_info['layout']}")
            else:
                logger.warning(f"Failed to generate slide {slide_info['slide_number']}")
                
        except Exception as e:
            logger.error(f"Error generating slide {slide_info['slide_number']}: {e}")
            continue
    
    logger.info(f"✅ Successfully generated {len(slides)} enhanced slides")
    return slides

def generate_slide_with_enhanced_context(slide_info, full_outline, template_id, content_data=None, processing_mode='preserve', input_method='topic'):
    """Generate individual slide with enhanced context from outline and source content"""
    
    layout = slide_info['layout']
    slide_number = slide_info['slide_number']
    total_slides = len(full_outline['slide_structure'])
    
    # Build enhanced context
    presentation_context = f"""
PRESENTATION CONTEXT:
Title: {full_outline['presentation_meta']['title']}
Objective: {full_outline['presentation_meta']['objective']}
Key Message: {full_outline['presentation_meta']['key_message']}
Input Method: {input_method}
Processing Mode: {processing_mode}

SLIDE POSITION: {slide_number} of {total_slides}

CURRENT SLIDE:
Purpose: {slide_info['purpose']}
Context: {slide_info['context']}
Key Points: {', '.join(slide_info.get('key_points', []))}

SLIDE FLOW:
Previous Transition: {slide_info['transitions']['from_previous'] or 'Opening slide'}
Next Transition: {slide_info['transitions']['to_next'] or 'Closing slide'}
"""

    # Add content context if available
    if content_data and input_method in ['text', 'document']:
        # Extract relevant content section for this slide
        relevant_content = extract_relevant_content_for_slide(
            content_data, slide_info, slide_number, total_slides
        )
        
        if relevant_content:
            presentation_context += f"""
SOURCE CONTENT SECTION:
{relevant_content[:1000]}{'...' if len(relevant_content) > 1000 else ''}

CONTENT PROCESSING:
Mode: {processing_mode}
Instruction: {'Preserve original wording and structure' if processing_mode == 'preserve' else 'Condense while maintaining key facts' if processing_mode == 'condense' else 'Enhance and expand with additional context'}
"""

    # Get surrounding slides context
    prev_slide = None
    next_slide = None
    
    for slide in full_outline['slide_structure']:
        if slide['slide_number'] == slide_number - 1:
            prev_slide = slide
        elif slide['slide_number'] == slide_number + 1:
            next_slide = slide
    
    if prev_slide:
        presentation_context += f"Previous Slide: {prev_slide['title']} - {prev_slide['purpose']}\n"
    if next_slide:
        presentation_context += f"Next Slide: {next_slide['title']} - {next_slide['purpose']}\n"
    
    # Create layout-specific prompts with enhanced context
    layout_prompts = {
        'titleOnly': f"""
{presentation_context}

Create a compelling title slide that sets the tone for the entire presentation.

Return ONLY this JSON:
{{"title": "Engaging title (max 60 chars)", "subtitle": "Compelling subtitle that previews the journey (max 120 chars)"}}

Title should be: {slide_info['title']}
Make it engaging and set proper expectations for the presentation flow.
""",

        'titleAndBullets': f"""
{presentation_context}

Create bullet points that advance the presentation narrative and connect to surrounding slides.

Return ONLY this JSON:
{{"title": "Clear section title (max 80 chars)", "bullets": ["Bullet 1 (max 150 chars)", "Bullet 2", "Bullet 3", "Bullet 4"]}}

Title should be: {slide_info['title']}
Create 3-5 bullets that flow logically and connect to the overall presentation arc.
{f'Extract and organize content from the source material above.' if content_data else ''}
""",

        'imageAndParagraph': f"""
{presentation_context}

Create detailed content that fits naturally in the presentation flow.

Return ONLY this JSON:
{{"title": "Descriptive title (max 80 chars)", "imageDescription": "Detailed image description (max 400 chars)", "paragraph": "Comprehensive explanation (max 400 chars)"}}

Title should be: {slide_info['title']}
Content should build on previous slides and prepare for upcoming content.
{f'Use relevant content from the source material to create an engaging paragraph.' if content_data else ''}
""",

        'conclusion': f"""
{presentation_context}

Create a strong conclusion that ties together the entire presentation.

Return ONLY this JSON:
{{"title": "Conclusion title (max 60 chars)", "summary": "Summary that reinforces key message (max 200 chars)", "nextSteps": ["Action 1 (max 50 chars)", "Action 2", "Action 3"]}}

Summarize the journey and provide clear, actionable next steps that align with the presentation objective.
{f'Draw conclusions from the source content and suggest practical next steps.' if content_data else ''}
""",

        'twoColumn': f"""
{presentation_context}

Create a two-column layout that presents complementary or contrasting information.

Return ONLY this JSON:
{{"title": "Comparison title (max 80 chars)", "column1Title": "Left column title (max 60 chars)", "column1Content": "Left content (max 300 chars)", "column2Title": "Right column title (max 60 chars)", "column2Content": "Right content (max 300 chars)"}}

Title should be: {slide_info['title']}
{f'Organize the source content into two logical sections that support the slide purpose.' if content_data else ''}
""",

        'quote': f"""
{presentation_context}

Create an impactful quote that reinforces the presentation message.

Return ONLY this JSON:
{{"quote": "Meaningful quote (max 200 chars)", "author": "Source or context (max 50 chars)"}}

{f'Extract a powerful quote from the source content or create one that captures its essence.' if content_data else 'Create an inspirational quote that fits the presentation theme.'}
""",

        'timeline': f"""
{presentation_context}

Create a timeline showing progression or development over time.

Return ONLY this JSON:
{{"title": "Timeline title (max 60 chars)", "events": [{{"year": "2020", "title": "Event name (max 40 chars)", "description": "Description (max 100 chars)"}}, {{"year": "2023", "title": "Event name", "description": "Description"}}]}}

Title should be: {slide_info['title']}
Focus on recent developments (2015-2025) and create a logical progression.
{f'Extract chronological information from the source content.' if content_data else ''}
"""
    }
    
    prompt = layout_prompts.get(layout, f"""
{presentation_context}

Create appropriate {layout} content that fits the presentation flow.
Title should be: {slide_info['title']}
Return valid JSON only.
""")
    
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            try:
                content_result = json.loads(generated_text)
                
                # Process content with enhanced context
                content_result['topic'] = full_outline['presentation_meta']['title']
                content_result['slide_index'] = slide_number
                content_result['total_slides'] = total_slides
                content_result['processing_mode'] = processing_mode
                
                return process_content_for_layout(content_result, layout)
                
            except json.JSONDecodeError:
                logger.warning(f"JSON decode error for enhanced slide {slide_number}")
                
    except Exception as e:
        logger.error(f"Error generating enhanced slide {slide_number}: {e}")
    
    # Enhanced fallback content generation
    return generate_enhanced_fallback_content(layout, slide_info, content_data, processing_mode)

def extract_relevant_content_for_slide(content_data, slide_info, slide_number, total_slides):
    """Extract relevant content section for a specific slide"""
    
    if not content_data or not content_data.get('full_text'):
        return None
    
    full_text = content_data['full_text']
    
    # Simple content sectioning based on slide position
    if total_slides <= 3:
        # For short presentations, use larger sections
        if slide_number == 1:
            return full_text[:1500]
        elif slide_number == total_slides:
            return full_text[-1000:]
        else:
            mid_point = len(full_text) // 2
            return full_text[mid_point-500:mid_point+500]
    else:
        # For longer presentations, divide more evenly
        content_slides = total_slides - 2  # Exclude title and conclusion
        if slide_number == 1:  # Title slide
            return full_text[:800]
        elif slide_number == total_slides:  # Conclusion slide
            return full_text[-1000:]
        else:
            # Content slides
            section_index = slide_number - 2
            section_size = len(full_text) // content_slides
            start_pos = section_index * section_size
            end_pos = min(len(full_text), start_pos + section_size + 500)  # Add overlap
            return full_text[start_pos:end_pos]

def validate_outline_structure_enhanced(outline, expected_slides):
    """Enhanced validation for outline structure"""
    try:
        # Check required top-level keys
        if not all(key in outline for key in ['presentation_meta', 'slide_structure']):
            return False
        
        # Check presentation meta
        meta = outline['presentation_meta']
        required_meta = ['title', 'objective', 'target_audience', 'key_message']
        if not all(key in meta for key in required_meta):
            return False
        
        # Check slide structure
        slides = outline['slide_structure']
        if not isinstance(slides, list) or len(slides) < 1:
            return False
        
        # Validate each slide
        required_slide_keys = ['slide_number', 'layout', 'title', 'purpose', 'context', 'transitions']
        for slide in slides:
            if not isinstance(slide, dict):
                return False
            
            if not all(key in slide for key in required_slide_keys):
                return False
            
            # Check transitions structure
            transitions = slide['transitions']
            if not isinstance(transitions, dict):
                return False
            
            if not all(key in transitions for key in ['from_previous', 'to_next']):
                return False
        
        return True
        
    except Exception:
        return False

    """Create enhanced fallback outline with content context"""
    
    slide_structure = []
    
    # Title slide
    slide_structure.append({
        "slide_number": 1,
        "layout": "titleOnly",
        "title": topic,
        "purpose": "Introduction",
        "key_points": ["Welcome", "Overview"],
        "context": f"Opening slide introducing the {input_method} presentation",
        "transitions": {
            "from_previous": None,
            "to_next": "Setting the foundation for our discussion"
        }
    })
    
    # Content slides with varied layouts
    content_layouts = ["titleAndBullets", "imageAndParagraph", "twoColumn", "quote"]
    
    for i in range(1, slide_count - 1):
        slide_num = i + 1
        layout = content_layouts[(i - 1) % len(content_layouts)]
        
        slide_structure.append({
            "slide_number": slide_num,
            "layout": layout,
            "title": f"Key Aspect {i} of {topic}",
            "purpose": f"Explore important element {i}",
            "key_points": [f"Point {i}.1", f"Point {i}.2", f"Point {i}.3"],
            "context": f"Detailed exploration of aspect {i} from {input_method}",
            "transitions": {
                "from_previous": "Building on previous concepts",
                "to_next": "Leading into next key area" if i < slide_count - 2 else "Moving toward conclusion"
            }
        })
    
    # Conclusion slide
    if slide_count > 1:
        slide_structure.append({
            "slide_number": slide_count,
            "layout": "conclusion",
            "title": f"Key Takeaways from {topic}",
            "purpose": "Conclusion and next steps",
            "key_points": ["Summary", "Next steps", "Call to action"],
            "context": f"Wrapping up insights from {input_method} and providing clear next steps",
            "transitions": {
                "from_previous": "Bringing together all our discussions",
                "to_next": None
            }
        })
    
    # Enhanced metadata based on input method
    if input_method == 'text':
        objective = f"Present and organize the key insights from the provided text about {topic}"
        audience = "Readers interested in the text content"
    elif input_method == 'document':
        objective = f"Communicate the main findings and recommendations from the document about {topic}"
        audience = "Stakeholders and decision-makers"
    else:
        objective = f"Provide comprehensive overview and analysis of {topic}"
        audience = "General audience interested in the topic"
    
    return {
        "presentation_meta": {
            "title": topic,
            "objective": objective,
            "target_audience": audience,
            "key_message": f"Understanding {topic} and its key implications"
        },
        "slide_structure": slide_structure
    }