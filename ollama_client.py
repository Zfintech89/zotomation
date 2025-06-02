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
logger = logging.getLogger("ollama_client")

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# ENHANCED MODE CONFIGURATIONS
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

def process_document_with_ollama(text, processing_mode, topic):
    """Process document through Ollama with proper mode handling"""
    
    mode_config = PROCESSING_MODES.get(processing_mode, PROCESSING_MODES['preserve'])
    
    logger.info(f"Processing document in {processing_mode} mode: {mode_config['name']}")
    
    cleaned_text = clean_input_text(text)
    
    if processing_mode == 'preserve':
        return preserve_document_structure(cleaned_text, topic, mode_config)
    elif processing_mode == 'condense':
        return condense_document_content(cleaned_text, topic, mode_config)
    elif processing_mode == 'generate':
        return enhance_document_content(cleaned_text, topic, mode_config)
    else:
        return preserve_document_structure(cleaned_text, topic, PROCESSING_MODES['preserve'])

def clean_input_text(text):
    """Clean and prepare input text for processing"""
    if not text:
        return ""
    
    # Remove page markers and clean up
    cleaned = re.sub(r'\[Page \d+\]', '', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Reduce excessive newlines
    cleaned = cleaned.strip()
    
    return cleaned

def preserve_document_structure(text, topic, mode_config):
    """Preserve mode: Keep original structure and content"""
    
    logger.info("Using PRESERVE mode - maintaining original content structure")
    
    # For preserve mode, we do minimal processing
    # Just analyze structure without changing content significantly
    
    structure_analysis = analyze_text_structure(text, topic)
    
    return {
        'processed_text': text,  # Keep original text unchanged
        'structure_analysis': structure_analysis,
        'processing_mode': 'preserve',
        'ollama_success': True,
        'mode_description': mode_config['description']
    }

def condense_document_content(text, topic, mode_config):
    """Condense mode: Intelligent summarization while keeping key facts"""
    
    logger.info("Using CONDENSE mode - intelligent summarization")
    
    # Limit text for processing
    limited_text = text[:3000] if len(text) > 3000 else text
    
    prompt = f"""You are an expert content summarizer. Your task is to condense the following document while preserving ALL key facts, statistics, and important information.

ORIGINAL DOCUMENT:
{limited_text}

TOPIC: {topic}

INSTRUCTIONS:
{mode_config['instruction']}

REQUIREMENTS:
- Keep all facts, numbers, and statistics exactly as they appear
- Preserve key terms and important phrases
- Maintain the logical flow and structure
- Remove redundant and filler content
- Make it 60-70% of original length
- Ensure readability and coherence

Return ONLY the condensed content, no explanations or metadata."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": mode_config['temperature'],
                    "top_p": mode_config['top_p'],
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            condensed_text = result.get("response", "").strip()
            
            if condensed_text and len(condensed_text) > 100:
                logger.info(f"Successfully condensed: {len(text)} → {len(condensed_text)} characters")
                
                structure_analysis = analyze_text_structure(condensed_text, topic)
                
                return {
                    'processed_text': condensed_text,
                    'structure_analysis': structure_analysis,
                    'processing_mode': 'condense',
                    'ollama_success': True,
                    'mode_description': mode_config['description']
                }
            else:
                logger.warning("Condense mode failed, using fallback")
                
    except Exception as e:
        logger.error(f"Condense mode error: {e}")
    
    # Fallback: Simple sentence-based condensing
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    condensed_fallback = '. '.join(sentences[:len(sentences)//2]) + '.'
    
    structure_analysis = analyze_text_structure(condensed_fallback, topic)
    
    return {
        'processed_text': condensed_fallback,
        'structure_analysis': structure_analysis,
        'processing_mode': 'condense_fallback',
        'ollama_success': False,
        'mode_description': mode_config['description']
    }

def enhance_document_content(text, topic, mode_config):
    """Generate mode: Enhance and expand content"""
    
    logger.info("Using GENERATE mode - enhancing and expanding content")
    
    # Limit text for processing
    limited_text = text[:2500] if len(text) > 2500 else text
    
    prompt = f"""You are an expert presentation content creator. Your task is to enhance the following document content to make it more engaging and comprehensive for a presentation.

ORIGINAL DOCUMENT:
{limited_text}

TOPIC: {topic}

INSTRUCTIONS:
{mode_config['instruction']}

REQUIREMENTS:
- Expand on key ideas with relevant context and examples
- Add engaging transitions and connecting phrases
- Maintain factual accuracy - don't invent statistics or facts
- Make content more presentation-friendly
- Improve clarity and flow
- Add relevant insights and implications
- Increase length by 20-40%
- Keep the enhanced content focused on the topic

Return ONLY the enhanced content, no explanations or metadata."""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": mode_config['temperature'],
                    "top_p": mode_config['top_p'],
                    "repeat_penalty": 1.0
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            enhanced_text = result.get("response", "").strip()
            
            if enhanced_text and len(enhanced_text) > len(text) * 0.8:  # Should be at least 80% of original
                logger.info(f"Successfully enhanced: {len(text)} → {len(enhanced_text)} characters")
                
                structure_analysis = analyze_text_structure(enhanced_text, topic)
                
                return {
                    'processed_text': enhanced_text,
                    'structure_analysis': structure_analysis,
                    'processing_mode': 'generate',
                    'ollama_success': True,
                    'mode_description': mode_config['description']
                }
            else:
                logger.warning("Generate mode failed, using fallback")
                
    except Exception as e:
        logger.error(f"Generate mode error: {e}")
    
    # Fallback: Add introduction and conclusion
    enhanced_fallback = f"""Enhanced Overview of {topic}

{text}

This comprehensive analysis provides valuable insights and actionable recommendations for understanding and addressing {topic} effectively. The key points presented here offer a foundation for further exploration and implementation."""
    
    structure_analysis = analyze_text_structure(enhanced_fallback, topic)
    
    return {
        'processed_text': enhanced_fallback,
        'structure_analysis': structure_analysis,
        'processing_mode': 'generate_fallback',
        'ollama_success': False,
        'mode_description': mode_config['description']
    }

def analyze_text_structure(text, topic):
    """Analyze text structure and determine optimal slide count and layout"""
    
    if not text:
        return generate_fallback_structure(3, topic)
    
    # Basic metrics
    word_count = len(text.split())
    paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
    sentence_count = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
    
    # Determine slide count based on content
    if word_count < 150:
        slide_count = 3
    elif word_count < 400:
        slide_count = 4
    elif word_count < 700:
        slide_count = 5
    elif word_count < 1000:
        slide_count = 6
    elif word_count < 1500:
        slide_count = 7
    else:
        slide_count = min(8, max(6, word_count // 200))
    
    # Generate structure plan
    structure_plan = generate_structure_plan(slide_count, text, topic)
    
    return {
        'recommended_slides': slide_count,
        'structure_plan': structure_plan,
        'reasoning': f'Determined {slide_count} slides based on {word_count} words, {paragraph_count} paragraphs',
        'content_metrics': {
            'words': word_count,
            'paragraphs': paragraph_count,
            'sentences': sentence_count
        }
    }

# REPLACEMENT FUNCTIONS for ollama_client.py

def generate_slides_from_ollama_analysis(processed_text, topic, template_id, structure_plan, processing_mode):
    """Generate slides using processed text and structure analysis - FIXED VERSION"""
    
    slides = []
    
    if not structure_plan:
        structure_plan = generate_fallback_structure(5, topic)['structure_plan']
    
    # Split text into sections for content slides
    content_slides = [item for item in structure_plan if item['layout'] not in ['titleOnly', 'conclusion']]
    text_sections = split_text_for_slides(processed_text, len(content_slides))
    
    mode_config = PROCESSING_MODES.get(processing_mode, PROCESSING_MODES['preserve'])
    
    for plan_item in structure_plan:
        slide_number = plan_item.get('slide_number', 1)
        layout = plan_item.get('layout', 'titleOnly')
        purpose = plan_item.get('purpose', '')
        
        logger.info(f"Generating slide {slide_number}: {layout} ({purpose})")
        
        try:
            if layout == 'titleOnly':
                # ALWAYS generate title slide - never skip
                content = generate_title_slide_content(topic, processed_text, processing_mode)
                
                # Ensure content is valid
                if not content or not content.get('title'):
                    content = {
                        'title': topic,
                        'subtitle': get_mode_subtitle(processing_mode, topic)
                    }
                
                slides.append({
                    'layout': 'titleOnly',
                    'content': content
                })
                logger.info(f"✅ Generated title slide: {content.get('title', 'No title')}")
                
            elif layout == 'conclusion':
                # ALWAYS generate conclusion slide - never skip
                conclusion_text = processed_text[-800:] if len(processed_text) > 800 else processed_text
                content = generate_conclusion_from_processed_text(conclusion_text, topic, processing_mode)
                
                # Ensure content is valid
                if not content or not content.get('title'):
                    content = {
                        'title': f"Key Takeaways - {topic}",
                        'summary': f"Important insights and conclusions from our analysis of {topic}.",
                        'nextSteps': get_mode_next_steps(processing_mode)
                    }
                
                slides.append({
                    'layout': 'conclusion',
                    'content': content
                })
                logger.info(f"✅ Generated conclusion slide: {content.get('title', 'No title')}")
                
            else:
                # Content slide - can be skipped if poor quality
                section_index = slide_number - 2
                if section_index < len(text_sections):
                    section_text = text_sections[section_index]
                else:
                    # Fallback to portion of full text
                    portion_size = len(processed_text) // max(1, len(content_slides))
                    start_pos = section_index * portion_size
                    end_pos = min(len(processed_text), start_pos + portion_size)
                    section_text = processed_text[start_pos:end_pos] if start_pos < len(processed_text) else processed_text
                
                content = generate_content_slide_from_processed_text(
                    layout, topic, section_text, slide_number, len(structure_plan), processing_mode
                )
                
                # Validate content quality for content slides
                if content and not is_generic_content(content):
                    slides.append({
                        'layout': layout,
                        'content': content
                    })
                    logger.info(f"✅ Generated {layout} slide with {len(str(content))} chars")
                else:
                    logger.warning(f"⚠️ Skipping {layout} slide due to poor content quality")
                
        except Exception as e:
            logger.error(f"❌ Error generating slide {slide_number} ({layout}): {e}")
            
            # For title and conclusion, provide fallback instead of skipping
            if layout == 'titleOnly':
                slides.append({
                    'layout': 'titleOnly',
                    'content': {
                        'title': topic,
                        'subtitle': get_mode_subtitle(processing_mode, topic)
                    }
                })
                logger.info(f"✅ Generated fallback title slide")
                
            elif layout == 'conclusion':
                slides.append({
                    'layout': 'conclusion',
                    'content': {
                        'title': f"Conclusion - {topic}",
                        'summary': f"Key insights from our analysis of {topic}.",
                        'nextSteps': get_mode_next_steps(processing_mode)
                    }
                })
                logger.info(f"✅ Generated fallback conclusion slide")
            
            # For content slides, we can skip
            continue
    
    # SAFETY CHECK: Ensure we always have at least title slide
    if not slides:
        logger.warning("⚠️ No slides generated, creating minimal presentation")
        slides = [
            {
                'layout': 'titleOnly',
                'content': {
                    'title': topic,
                    'subtitle': get_mode_subtitle(processing_mode, topic)
                }
            }
        ]
    
    # SAFETY CHECK: Ensure title slide is first
    title_slides = [s for s in slides if s['layout'] == 'titleOnly']
    if not title_slides:
        logger.warning("⚠️ Missing title slide, adding one")
        slides.insert(0, {
            'layout': 'titleOnly',
            'content': {
                'title': topic,
                'subtitle': get_mode_subtitle(processing_mode, topic)
            }
        })
    
    # SAFETY CHECK: Ensure conclusion slide is last (for presentations with 3+ slides)
    if len(slides) >= 3:
        conclusion_slides = [s for s in slides if s['layout'] == 'conclusion']
        if not conclusion_slides:
            logger.warning("⚠️ Missing conclusion slide, adding one")
            slides.append({
                'layout': 'conclusion',
                'content': {
                    'title': f"Key Takeaways - {topic}",
                    'summary': f"Important insights from our analysis of {topic}.",
                    'nextSteps': get_mode_next_steps(processing_mode)
                }
            })
    
    logger.info(f"✅ Generated {len(slides)} valid slides in {processing_mode} mode")
    return slides

def get_mode_subtitle(processing_mode, topic):
    """Get appropriate subtitle based on processing mode"""
    subtitles = {
        'preserve': 'Document Analysis and Original Insights',
        'condense': 'Key Points and Essential Information',
        'generate': 'Comprehensive Analysis and Strategic Overview'
    }
    return subtitles.get(processing_mode, f'Analysis of {topic}')

def get_mode_next_steps(processing_mode):
    """Get appropriate next steps based on processing mode"""
    next_steps = {
        'preserve': [
            'Review documented findings',
            'Implement key recommendations',
            'Monitor progress and outcomes'
        ],
        'condense': [
            'Focus on priority actions',
            'Apply essential insights',
            'Track key metrics'
        ],
        'generate': [
            'Develop comprehensive strategy',
            'Engage stakeholders effectively',
            'Execute with measurable results'
        ]
    }
    return next_steps.get(processing_mode, [
        'Review key findings',
        'Plan implementation',
        'Monitor progress'
    ])

def generate_title_slide_content(topic, processed_text, processing_mode):
    """Generate title slide content - IMPROVED VERSION"""
    
    logger.info(f"Generating title slide in {processing_mode} mode")
    
    # Extract potential title from content for preserve mode
    if processing_mode == 'preserve' and processed_text:
        lines = [line.strip() for line in processed_text.split('\n') if line.strip()]
        
        # Look for a good title in the first few lines
        for line in lines[:3]:
            if 10 < len(line) < 100 and not line.endswith('.') and len(line.split()) < 15:
                return {
                    'title': line,
                    'subtitle': 'Document Analysis and Key Insights'
                }
    
    # Mode-specific titles and subtitles
    if processing_mode == 'preserve':
        return {
            'title': topic,
            'subtitle': 'Document Analysis and Original Insights'
        }
    elif processing_mode == 'condense':
        return {
            'title': topic,
            'subtitle': 'Essential Points and Key Information'
        }
    else:  # generate mode
        return {
            'title': topic,
            'subtitle': 'Comprehensive Analysis and Strategic Overview'
        }

def generate_conclusion_from_processed_text(conclusion_text, topic, processing_mode):
    """Generate conclusion content - IMPROVED VERSION"""
    
    logger.info(f"Generating conclusion slide in {processing_mode} mode")
    
    if processing_mode == 'preserve':
        # Try to extract actual conclusions from the text
        sentences = [s.strip() for s in conclusion_text.split('.') if s.strip()]
        
        # Look for conclusion keywords
        conclusion_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['conclusion', 'summary', 'therefore', 'in summary', 'overall']):
                conclusion_sentences.append(sentence)
        
        if conclusion_sentences:
            summary = '. '.join(conclusion_sentences[:2]) + '.'
        else:
            summary = '. '.join(sentences[:2]) + '.' if len(sentences) >= 2 else conclusion_text[:200]
        
        return {
            'title': 'Key Findings',
            'summary': summary,
            'nextSteps': [
                'Review documented findings',
                'Implement key recommendations',
                'Follow up on action items'
            ]
        }
    
    elif processing_mode == 'condense':
        return {
            'title': 'Essential Takeaways',
            'summary': f'Core insights and critical findings from the analysis of {topic}.',
            'nextSteps': [
                'Focus on priority actions',
                'Apply key learnings immediately',
                'Track essential metrics'
            ]
        }
    
    else:  # generate mode
        return {
            'title': 'Strategic Path Forward',
            'summary': f'Our comprehensive analysis of {topic} reveals significant opportunities and actionable strategies for success.',
            'nextSteps': [
                'Develop comprehensive implementation plan',
                'Engage key stakeholders and teams',
                'Execute with clear measurable outcomes'
            ]
        }

def is_generic_content(content):
    """Check if content is generic - IMPROVED VERSION"""
    if not isinstance(content, dict):
        return True
    
    # Less strict for title and conclusion slides
    layout_context = content.get('_layout_hint', '')
    
    if layout_context in ['titleOnly', 'conclusion']:
        # More lenient validation for title and conclusion
        generic_indicators = ['placeholder', 'insert content here', 'example text']
    else:
        # Stricter validation for content slides
        generic_indicators = [
            'placeholder', 'example content', 'insert here', 'page 1', 
            'section 1', 'content goes here', 'sample text'
        ]
    
    content_str = str(content).lower()
    
    for indicator in generic_indicators:
        if indicator in content_str:
            logger.debug(f"Found generic indicator: {indicator}")
            return True
    
    return False

def validate_content_quality(content, layout):
    """Validate content quality - IMPROVED VERSION"""
    if not isinstance(content, dict):
        return False
    
    # Add layout hint for better validation
    content['_layout_hint'] = layout
    
    # More lenient validation for title and conclusion
    if layout in ['titleOnly', 'conclusion']:
        if layout == 'titleOnly':
            return (content.get('title') and len(content.get('title', '')) > 3)
        elif layout == 'conclusion':
            return (content.get('title') and len(content.get('title', '')) > 3 and
                   (content.get('summary') or content.get('nextSteps')))
    
    # Stricter validation for content slides
    if layout == 'titleAndBullets':
        return (content.get('title') and len(content.get('title', '')) > 5 and
                content.get('bullets') and len(content.get('bullets', [])) >= 2 and
                all(len(str(b)) > 10 for b in content.get('bullets', [])[:3]))
    
    elif layout == 'imageAndParagraph':
        return (content.get('title') and len(content.get('title', '')) > 5 and
                content.get('paragraph') and len(content.get('paragraph', '')) > 30)
    
    elif layout == 'twoColumn':
        return (content.get('title') and len(content.get('title', '')) > 5 and
                content.get('column1Content') and len(content.get('column1Content', '')) > 20 and
                content.get('column2Content') and len(content.get('column2Content', '')) > 20)
    
    return True

# ALSO ADD this function to fix the structure generation
def generate_structure_plan(slide_count, text, topic):
    """Generate slide structure plan - FIXED VERSION"""
    
    structure = []
    
    # ALWAYS start with title slide
    structure.append({
        "slide_number": 1,
        "layout": "titleOnly",
        "purpose": "Introduction and title",
        "content_focus": f"Title and overview of {topic}"
    })
    
    # Content slides (only if we have more than 2 slides total)
    content_slides_needed = max(0, slide_count - 2)  # Exclude title and conclusion
    
    if content_slides_needed > 0:
        layouts = ["titleAndBullets", "imageAndParagraph", "twoColumn", "timeline", "imageWithFeatures"]
        
        for i in range(content_slides_needed):
            slide_num = i + 2  # Start from slide 2
            layout = layouts[i % len(layouts)]
            
            structure.append({
                "slide_number": slide_num,
                "layout": layout,
                "purpose": f"Content section {i + 1}",
                "content_focus": f"Key points and details - section {i + 1}"
            })
    
    # ALWAYS end with conclusion slide (if we have 3+ slides total)
    if slide_count >= 3:
        structure.append({
            "slide_number": slide_count,
            "layout": "conclusion", 
            "purpose": "Summary and next steps",
            "content_focus": "Key takeaways and action items"
        })
    elif slide_count == 2:
        # For 2-slide presentations, second slide is conclusion
        structure.append({
            "slide_number": 2,
            "layout": "conclusion",
            "purpose": "Summary and conclusions",
            "content_focus": "Key takeaways"
        })
    
    logger.info(f"Generated structure plan: {len(structure)} slides")
    for item in structure:
        logger.info(f"  Slide {item['slide_number']}: {item['layout']} - {item['purpose']}")
    
    return structure

def generate_content_slide_from_processed_text(layout, topic, section_text, slide_number, total_slides, processing_mode):
    """Generate content slide from processed text based on mode"""
    
    if not section_text or len(section_text.strip()) < 20:
        return generate_fallback_content(layout, topic, slide_number)
    
    mode_config = PROCESSING_MODES.get(processing_mode, PROCESSING_MODES['preserve'])
    
    if processing_mode == 'preserve':
        # Extract content directly from text
        return extract_content_intelligently(layout, topic, section_text, slide_number, total_slides)
    
    else:
        # Use AI generation for condense/generate modes
        return generate_content_with_ai(layout, topic, section_text, slide_number, total_slides, mode_config)

def extract_content_intelligently(layout, topic, source_text, slide_index, total_slides):
    """Intelligently extract content preserving original structure"""
    
    lines = [line.strip() for line in source_text.split('\n') if line.strip()]
    paragraphs = [p.strip() for p in source_text.split('\n\n') if p.strip()]
    
    # Find potential titles
    potential_titles = []
    for line in lines[:5]:
        if len(line) < 80 and not line.endswith('.') and len(line.split()) < 12:
            potential_titles.append(line)
    
    main_title = potential_titles[0] if potential_titles else f"Section {slide_index - 1}"
    
    if layout == 'titleAndBullets':
        bullets = extract_bullet_points(source_text)
        if not bullets:
            bullets = extract_key_sentences(source_text, 4)
        
        return {
            'title': main_title,
            'bullets': bullets[:5]
        }
    
    elif layout == 'imageAndParagraph':
        best_paragraph = find_best_paragraph(paragraphs)
        
        return {
            'title': main_title,
            'imageDescription': f"Visual representation related to {main_title.lower()}",
            'paragraph': best_paragraph
        }
    
    elif layout == 'twoColumn':
        half_point = len(paragraphs) // 2
        first_half = paragraphs[:half_point] if half_point > 0 else paragraphs[:1]
        second_half = paragraphs[half_point:] if half_point > 0 else paragraphs[1:]
        
        return {
            'title': main_title,
            'column1Title': 'Key Points',
            'column1Content': '\n\n'.join(first_half)[:300],
            'column2Title': 'Additional Details',
            'column2Content': '\n\n'.join(second_half)[:300]
        }
    
    # Add more layout handling as needed
    return generate_fallback_content(layout, topic, slide_index)

def extract_bullet_points(text):
    """Extract existing bullet points from text"""
    bullets = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if (line.startswith(('•', '-', '*')) or re.match(r'^\d+[\.\)]\s+', line)):
            cleaned = re.sub(r'^[•\-*\d\.\)\s]+', '', line).strip()
            if cleaned and len(cleaned) > 10:
                bullets.append(cleaned)
    
    return bullets

def extract_key_sentences(text, max_sentences=4):
    """Extract key sentences as bullet points"""
    sentences = []
    for sent in re.split(r'[.!?]+', text):
        sent = sent.strip()
        if 20 < len(sent) < 150:  # Good sentence length
            sentences.append(sent)
    
    return sentences[:max_sentences]

def find_best_paragraph(paragraphs):
    """Find the most substantial paragraph"""
    best_paragraph = ""
    
    for para in paragraphs:
        if 100 < len(para) < 400:  # Good paragraph length
            best_paragraph = para
            break
    
    if not best_paragraph and paragraphs:
        best_paragraph = paragraphs[0]
    
    return best_paragraph or "Key information extracted from the document."

def generate_content_with_ai(layout, topic, section_text, slide_number, total_slides, mode_config):
    """Generate content using AI for condense/generate modes"""
    
    limited_text = section_text[:1500] if len(section_text) > 1500 else section_text
    
    layout_prompts = create_layout_specific_prompts(layout, topic, limited_text, mode_config)
    prompt = layout_prompts.get(layout, "")
    
    if not prompt:
        return extract_content_intelligently(layout, topic, section_text, slide_number, total_slides)
    
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": mode_config['temperature'],
                    "top_p": mode_config['top_p'],
                    "repeat_penalty": 1.1
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            content_result = extract_clean_json(generated_text, layout)
            
            if content_result and validate_content_quality(content_result, layout):
                return content_result
            else:
                logger.warning(f"AI generation failed for {layout}, using extraction fallback")
                
    except Exception as e:
        logger.error(f"AI generation error for {layout}: {e}")
    
    # Fallback to intelligent extraction
    return extract_content_intelligently(layout, topic, section_text, slide_number, total_slides)

def create_layout_specific_prompts(layout, topic, source_text, mode_config):
    """Create specific prompts for each layout and mode"""
    
    base_instruction = mode_config['instruction']
    
    prompts = {
        'titleAndBullets': f"""
{base_instruction}

SOURCE CONTENT:
{source_text}

TOPIC: {topic}

Create a title and 3-5 bullet points. Extract key information while following the mode instructions.

Return ONLY this JSON:
{{"title": "Clear slide title", "bullets": ["Point 1", "Point 2", "Point 3"]}}
""",

        'imageAndParagraph': f"""
{base_instruction}

SOURCE CONTENT:
{source_text}

TOPIC: {topic}

Create a title, image description, and descriptive paragraph. Follow the mode instructions for content processing.

Return ONLY this JSON:
{{"title": "Slide title", "imageDescription": "Professional image description", "paragraph": "Detailed paragraph content"}}
""",

        'twoColumn': f"""
{base_instruction}

SOURCE CONTENT:
{source_text}

TOPIC: {topic}

Split the content into two complementary sections. Follow the mode instructions for processing.

Return ONLY this JSON:
{{"title": "Comparison title", "column1Title": "Left section", "column1Content": "Left content", "column2Title": "Right section", "column2Content": "Right content"}}
"""
    }
    
    return prompts

def split_text_for_slides(text, num_sections):
    """Split text into sections for slides"""
    if not text or num_sections <= 0:
        return [""]
    
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if len(paragraphs) <= num_sections:
        return paragraphs + [""] * (num_sections - len(paragraphs))
    
    sections = []
    paras_per_section = len(paragraphs) // num_sections
    remainder = len(paragraphs) % num_sections
    
    start = 0
    for i in range(num_sections):
        section_size = paras_per_section + (1 if i < remainder else 0)
        end = start + section_size
        
        section_paras = paragraphs[start:end]
        sections.append('\n\n'.join(section_paras))
        
        start = end
    
    return sections

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

def generate_fallback_content(layout, topic, slide_index):
    """Generate fallback content for failed cases"""
    
    if layout == 'titleAndBullets':
        return {
            'title': f"{topic} - Key Points",
            'bullets': [
                f"Important aspect of {topic}",
                f"Key consideration for implementation",
                f"Critical success factor"
            ]
        }
    elif layout == 'imageAndParagraph':
        return {
            'title': f"{topic} Overview",
            'imageDescription': f"Professional visualization of {topic}",
            'paragraph': f"This section covers important information about {topic} and its key implications."
        }
    elif layout == 'twoColumn':
        return {
            'title': f"{topic} Analysis",
            'column1Title': "Key Points",
            'column1Content': f"Important aspects of {topic}",
            'column2Title': "Implications",
            'column2Content': f"Strategic considerations for {topic}"
        }
    
    return {}

def generate_fallback_structure(slide_count, topic):
    """Generate fallback structure"""
    return {
        'recommended_slides': slide_count,
        'structure_plan': [
            {"slide_number": 1, "layout": "titleOnly", "purpose": "Introduction"},
            {"slide_number": 2, "layout": "titleAndBullets", "purpose": "Key points"},
            {"slide_number": slide_count, "layout": "conclusion", "purpose": "Summary"}
        ],
        'reasoning': f'Fallback structure with {slide_count} slides'
    }



def clean_extracted_title(title):
    """Clean up extracted titles"""
    if not title:
        return "Content"
    
    # Remove common artifacts
    title = re.sub(r'^[•\-*\d\.]\s*', '', title)  # Remove bullet markers
    title = re.sub(r':$', '', title)  # Remove trailing colons
    title = title.strip()
    
    # Capitalize properly
    if title.islower():
        title = title.title()
    
    return title

def clean_bullet_text(text):
    """Clean up extracted bullet points"""
    if not text:
        return ""
    
    text = re.sub(r'^[•\-*\d\.]\s*', '', text)
    text = text.strip()
    
    if text and not text.endswith(('.', '!', '?')):
        text += '.'
    
    return text


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

DEFAULT_DOCUMENT_MODE = 'preserve'  # Changed from 'generate'

# ADD THE MISSING FUNCTION
def create_other_mode_prompts(layout, limited_text, processing_mode, slide_context):
    """Create prompts for non-preserve modes"""
    mode_config = CONTENT_PRESERVATION_MODES.get(processing_mode, CONTENT_PRESERVATION_MODES['generate'])
    
    base_instruction = mode_config['instruction']
    
    # Create prompts for different modes
    if processing_mode == 'condense':
        prompt_prefix = f"""
{base_instruction}

SOURCE TEXT:
{limited_text}

TASK: Condense and summarize the above content for a {layout} slide layout.
Focus on {slide_context}.
"""
    else:  # generate mode
        prompt_prefix = f"""
{base_instruction}

SOURCE TEXT (for inspiration):
{limited_text}

TASK: Create enhanced content for a {layout} slide layout based on the source material.
Focus on {slide_context}.
"""
    
    # Layout-specific instructions
    layout_instructions = get_layout_specific_prompt(layout)
    
    return {layout: f"{prompt_prefix}\n\n{layout_instructions}"}

# Add this new function to ollama_client.py

def analyze_document_structure(full_text, topic):
    """
    Let Ollama analyze the document and decide the optimal slide structure
    Returns: slide count, slide structure plan, and content sections
    """
    
    # Limit text for analysis (first 2000 chars for overview)
    analysis_text = full_text[:2000] if len(full_text) > 2000 else full_text
    
    structure_prompt = f"""You are an expert presentation designer. Analyze this document content and determine the optimal presentation structure.

DOCUMENT CONTENT:
{analysis_text}

TOPIC: {topic}

TASK: Analyze this content and determine:
1. How many slides this presentation should have (minimum 3, maximum 12)
2. What should be the structure and flow of slides
3. What main topics/sections should each slide cover

REQUIREMENTS:
- Always start with a title slide
- Always end with a conclusion slide  
- Content slides should logically flow from the document
- Each slide should have enough content to be meaningful
- Avoid too many slides (max 12) or too few (min 3)

Return your analysis as JSON in this exact format:
{{
    "slide_count": number,
    "structure": [
        {{"slide_number": 1, "layout": "titleOnly", "purpose": "Introduction and title", "main_content": "Title and overview"}},
        {{"slide_number": 2, "layout": "titleAndBullets", "purpose": "First main topic", "main_content": "Key points about..."}},
        {{"slide_number": 3, "layout": "imageAndParagraph", "purpose": "Second main topic", "main_content": "Details about..."}},
        {{"slide_number": 4, "layout": "conclusion", "purpose": "Summary and next steps", "main_content": "Key takeaways and actions"}}
    ],
    "reasoning": "Brief explanation of why this structure works for this content"
}}

AVAILABLE LAYOUTS: titleOnly, titleAndBullets, quote, imageAndParagraph, twoColumn, imageWithFeatures, numberedFeatures, benefitsGrid, iconGrid, sideBySideComparison, timeline, conclusion

Analyze the content and return the optimal presentation structure as JSON only."""

    try:
        logging.info(f"Analyzing document structure for topic: {topic}")
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.1:8b", "prompt": structure_prompt, "stream": False}
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            # Extract JSON from response
            structure_result = extract_clean_json(generated_text, "structure_analysis")
            
            if structure_result and 'slide_count' in structure_result:
                slide_count = structure_result['slide_count']
                structure = structure_result.get('structure', [])
                reasoning = structure_result.get('reasoning', '')
                
                # Validate slide count
                slide_count = max(3, min(12, int(slide_count)))
                
                logging.info(f"Ollama determined slide count: {slide_count}")
                logging.info(f"Reasoning: {reasoning}")
                
                return {
                    'slide_count': slide_count,
                    'structure': structure,
                    'reasoning': reasoning,
                    'success': True
                }
            else:
                logging.warning("Failed to parse structure analysis from Ollama")
                
    except Exception as e:
        logging.error(f"Error in document structure analysis: {e}")
    
    # Fallback: intelligent slide count based on content length
    fallback_count = calculate_fallback_slide_count(full_text)
    logging.info(f"Using fallback slide count: {fallback_count}")
    
    return {
        'slide_count': fallback_count,
        'structure': generate_fallback_structure(fallback_count, topic),
        'reasoning': 'Fallback structure based on content length',
        'success': False
    }

def calculate_fallback_slide_count(text):
    """Calculate slide count based on content metrics"""
    if not text:
        return 3
    
    word_count = len(text.split())
    paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
    
    if word_count < 200:
        return 3
    elif word_count < 500:
        return 4
    elif word_count < 800:
        return 5
    elif word_count < 1200:
        return 6
    elif word_count < 1600:
        return 7
    elif word_count < 2000:
        return 8
    else:
        return min(10, max(8, word_count // 250))

def generate_fallback_structure(slide_count, topic):
    """Generate fallback structure if Ollama analysis fails"""
    available_layouts = [
        "titleAndBullets", "imageAndParagraph", "twoColumn",
        "imageWithFeatures", "numberedFeatures", "timeline"
    ]
    
    structure = []
    
    # Title slide
    structure.append({
        "slide_number": 1,
        "layout": "titleOnly", 
        "purpose": "Introduction",
        "main_content": f"Title and overview of {topic}"
    })
    
    # Content slides
    for i in range(2, slide_count):
        layout = available_layouts[(i-2) % len(available_layouts)]
        structure.append({
            "slide_number": i,
            "layout": layout,
            "purpose": f"Content section {i-1}",
            "main_content": f"Main topic {i-1} from document"
        })
    
    # Conclusion slide
    structure.append({
        "slide_number": slide_count,
        "layout": "conclusion",
        "purpose": "Summary and conclusions", 
        "main_content": "Key takeaways and next steps"
    })
    
    return structure
# COMPLETE FIX for all processing modes in ollama_client.py

def generate_content_from_text(layout, topic, source_text, slide_index, total_slides, processing_mode='preserve'):
    """Generate content using ALL processing modes with proper fallbacks"""
    
    logger.info(f"Generating {layout} content (slide {slide_index}/{total_slides}) in {processing_mode} mode")
    
    if processing_mode == 'preserve':
        # Use direct intelligent extraction (already working)
        return extract_content_intelligently(layout, topic, source_text, slide_index, total_slides)
    
    elif processing_mode in ['condense', 'generate']:
        # Try AI generation first, with intelligent fallback
        ai_content = generate_with_ai_modes(layout, topic, source_text, slide_index, total_slides, processing_mode)
        
        if ai_content and not is_generic_content(ai_content):
            logger.info(f"Successfully generated {layout} content via AI in {processing_mode} mode")
            return ai_content
        else:
            logger.warning(f"AI {processing_mode} mode failed, falling back to intelligent extraction")
            return extract_content_intelligently(layout, topic, source_text, slide_index, total_slides)
    
    else:
        # Unknown mode - default to preserve
        logger.warning(f"Unknown processing mode: {processing_mode}, defaulting to preserve")
        return extract_content_intelligently(layout, topic, source_text, slide_index, total_slides)

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


def generate_content(layout, topic, slide_index=None, total_slides=None):
    """Generate slide content with improved context handling"""
    escaped_topic = topic.replace(":", " - ").replace("{", "(").replace("}", ")").replace('"', "'")
    
    slide_context = ""
    focus_area = ""
    
    if slide_index is not None and total_slides is not None:
        slide_context = f" This is slide {slide_index} of {total_slides}."
        
        if slide_index == 1:
            focus_area = "introduction and overview"
        elif slide_index == total_slides:
            focus_area = "conclusions and next steps"
        elif slide_index == 2:
            focus_area = "main concepts and key information"
        else:
            aspects = [
                "important considerations and implications",
                "real-world applications and case studies", 
                "current challenges and effective solutions",
                "statistical data and measurable outcomes",
                "historical development and evolution",
                "future trends and emerging developments",
                "practical implementation strategies"
            ]
            focus_area = aspects[(slide_index - 3) % len(aspects)]
        
        slide_context += f" Focus on {focus_area}."

    CHAR_LIMITS = {
        'titleOnly': {'title': 60, 'subtitle': 120},
        'titleAndBullets': {'title': 80, 'bullets': 150},
        'quote': {'quote': 200, 'author': 50},
        'imageAndParagraph': {'title': 80, 'paragraph': 300, 'imageDescription': 1000},  # INCREASED FOR DETAILED PROMPTS
        'twoColumn': {'title': 80, 'column1Title': 60, 'column2Title': 60, 'column1Content': 300, 'column2Content': 300},
        'imageWithFeatures': {'title': 80, 'imageDescription': 1000, 'feature_title': 40, 'feature_description': 50},  # INCREASED FOR DETAILED PROMPTS
        'numberedFeatures': {'title': 80, 'imageDescription': 1000, 'feature_title': 40, 'feature_description': 100},  # INCREASED FOR DETAILED PROMPTS
        'benefitsGrid': {'title': 60, 'imageDescription': 1000, 'benefit_title': 30, 'benefit_description': 60},  # INCREASED FOR DETAILED PROMPTS
        'iconGrid': {'title': 60, 'category_name': 25, 'category_description': 40},
        'sideBySideComparison': {'title': 80, 'leftTitle': 40, 'rightTitle': 40, 'point': 120},
        'timeline': {'title': 60, 'event_title': 40, 'event_description': 100},
        'conclusion': {'title': 60, 'summary': 100, 'next_step': 50},
    }

    limits = CHAR_LIMITS.get(layout, {})
    
    prompts = {

        "imageWithFeatures": f"""Create a slide about '{escaped_topic}' with image and 4 features.{slide_context}

        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 80)} characters
        - 'imageDescription': Maximum {limits.get('imageDescription', 400)} characters
        - Each feature 'title': Maximum {limits.get('feature_title', 40)} characters
        - Each feature 'description': Maximum {limits.get('feature_description', 80)} characters

        TITLE GUIDELINES:
        - Create a specific, action-oriented title
        - Avoid generic words like "Key Features" or "Main Points"

        Format as JSON with ONLY these fields:
        - "title": Specific title (under {limits.get('title', 80)} chars)
        - "imageDescription": Image description (under {limits.get('imageDescription', 400)} chars)
        - "features": Array of exactly 4 objects, each with:
        - "title": Feature name (under {limits.get('feature_title', 40)} chars)
        - "description": Feature description (under {limits.get('feature_description', 80)} chars)

        Example: {{"title": "Combating Gender Discrimination", "imageDescription": "Diverse workplace with equal representation", "features": [{{"title": "Policy Development", "description": "Implement clear anti-discrimination policies and procedures"}}, {{"title": "Training Programs", "description": "Conduct regular bias awareness and inclusion training"}}, {{"title": "Pay Equity", "description": "Regular salary audits to ensure equal pay practices"}}, {{"title": "Reporting Systems", "description": "Safe channels for reporting discrimination incidents"}}]}}""",

        "numberedFeatures": f"""Create a slide with 4 numbered features about '{escaped_topic}'.{slide_context}

        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 80)} characters
        - 'imageDescription': Maximum {limits.get('imageDescription', 400)} characters
        - Each feature 'title': Maximum {limits.get('feature_title', 40)} characters
        - Each feature 'description': Maximum {limits.get('feature_description', 80)} characters

        Format as JSON with ONLY these fields:
        - 'title': Compelling title (under {limits.get('title', 80)} chars)
        - 'imageDescription': Brief image description (under {limits.get('imageDescription', 800)} chars)
        - 'features': Array of exactly 4 objects, each with:
        - 'number': String number ('1', '2', '3', '4')
        - 'title': Feature title (under {limits.get('feature_title', 40)} chars)
        - 'description': Feature description (under {limits.get('feature_description', 100)} chars)

        Example: {{"title": "Breaking Down Gender Barriers", "imageDescription": "Professional women in leadership roles", "features": [{{"number": "1", "title": "Equal Opportunities", "description": "Ensure fair hiring and promotion practices"}}, {{"number": "2", "title": "Mentorship Programs", "description": "Connect women with senior leadership mentors"}}, {{"number": "3", "title": "Flexible Policies", "description": "Support work-life balance for all employees"}}, {{"number": "4", "title": "Accountability", "description": "Track and report diversity metrics regularly"}}]}}""",

        "benefitsGrid": f"""Create a slide about benefits of addressing '{escaped_topic}'.{slide_context}

        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 60)} characters
        - 'imageDescription': Maximum {limits.get('imageDescription', 400)} characters
        - Each benefit 'title': Maximum {limits.get('benefit_title', 30)} characters
        - Each benefit 'description': Maximum {limits.get('benefit_description', 60)} characters

        Format as JSON with ONLY these fields:
        - 'title': Positive title (under {limits.get('title', 60)} chars)
        - 'imageDescription': Image description (under {limits.get('imageDescription', 800)} chars)
        - 'benefits': Array of exactly 4 objects, each with:
        - 'title': SHORT benefit name (under {limits.get('benefit_title', 30)} chars)
        - 'description': Brief explanation (under {limits.get('benefit_description', 60)} chars)

        Example: {{"title": "Creating Inclusive Workplaces", "imageDescription": "Diverse team collaborating successfully", "benefits": [{{"title": "Better Performance", "description": "Teams with gender diversity perform 25% better"}}, {{"title": "Higher Innovation", "description": "Diverse perspectives drive creative solutions"}}, {{"title": "Talent Retention", "description": "Inclusive cultures reduce employee turnover"}}, {{"title": "Legal Protection", "description": "Compliance reduces discrimination lawsuits"}}]}}""",

        "titleOnly": f"""Create a compelling title slide about '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 60)} characters
        - 'subtitle': Maximum {limits.get('subtitle', 120)} characters
        
        TITLE GUIDELINES:
        - Create a clean, professional title without prefixes like "Introduction to" or slide numbers
        - Make it engaging and directly related to the topic
        - Avoid generic words like "Overview", "Examples", "Statistics" at the beginning
        
        
        Format as JSON with ONLY these keys:
        - 'title': A compelling main title (under {limits.get('title', 60)} chars)
        - 'subtitle': A descriptive subtitle (under {limits.get('subtitle', 120)} chars)
        
        Example: {{"title": "Gender Discrimination", "subtitle": "Understanding Workplace Inequality and Solutions"}}""",

        "titleAndBullets": f"""Create a slide with title and 3-5 bullet points about '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 80)} characters
        - Each bullet: Maximum {limits.get('bullets', 150)} characters
        
        TITLE GUIDELINES:
        - Create a natural, engaging title without awkward prefixes
        - Avoid starting with "Examples", "Key Points", "Statistics", etc.
        - Make it specific to the focus area but naturally worded
        
        Format as JSON with ONLY these fields:
        - 'title': Clear, natural title (under {limits.get('title', 80)} chars)
        - 'bullets': Array of 3-5 complete points (each under {limits.get('bullets', 150)} chars)
        
        Example: {{"title": "Workplace Gender Discrimination", "bullets": ["Women earn 82 cents for every dollar earned by men", "Only 27% of senior leadership roles are held by women", "Pregnancy discrimination affects 1 in 4 working mothers"]}}""",

        "quote": f"""Create an inspirational quote about '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'quote': Maximum {limits.get('quote', 200)} characters
        - 'author': Maximum {limits.get('author', 50)} characters
        
        Format as JSON with ONLY these fields:
        - 'quote': Meaningful quotation (under {limits.get('quote', 200)} chars)
        - 'author': Real person's name (under {limits.get('author', 50)} chars)
        
        Example: {{"quote": "Equality is not a women's issue, it's a human issue. It affects us all.", "author": "Gloria Steinem"}}""",

        "imageAndParagraph": f"""Create a slide about '{escaped_topic}' with image and text.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 80)} characters
        - 'imageDescription': Maximum {limits.get('imageDescription', 800)} characters  
        - 'paragraph': Maximum {limits.get('paragraph', 400)} characters
        
        TITLE GUIDELINES:
        - Create a clear, specific title without generic prefixes
        - Focus on the main concept rather than using words like "About" or "Introduction"

        Do not include any metadata in the response.
        
        Format as JSON with ONLY these fields:
        - 'title': Clear title (under {limits.get('title', 80)} chars)
        - 'imageDescription': Specific image description (under {limits.get('imageDescription', 400)} chars)
        - 'paragraph': Detailed explanation (under {limits.get('paragraph', 400)} chars)
        
        Example: {{"title": "Gender Pay Gap Realities", "imageDescription": "Professional workplace showing diverse employees", "paragraph": "Despite decades of progress, gender discrimination in the workplace remains a persistent issue. Women continue to face barriers in hiring, promotion, and compensation across various industries."}}""",

        "twoColumn": f"""Create a slide comparing two aspects of '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 80)} characters
        - 'column1Title': Maximum {limits.get('column1Title', 60)} characters
        - 'column2Title': Maximum {limits.get('column2Title', 60)} characters
        - 'column1Content': Maximum {limits.get('column1Content', 300)} characters
        - 'column2Content': Maximum {limits.get('column2Content', 300)} characters
        
        TITLE GUIDELINES:
        - Create a natural comparison title without "vs" or "Traditional vs Modern" patterns
        - Make it specific and engaging
        
        Format as JSON with ONLY these fields:
        - 'title': Natural comparison title (under {limits.get('title', 80)} chars)
        - 'column1Title': Left column title (under {limits.get('column1Title', 60)} chars)
        - 'column1Content': Left column content (under {limits.get('column1Content', 300)} chars)
        - 'column2Title': Right column title (under {limits.get('column2Title', 60)} chars)
        - 'column2Content': Right column content (under {limits.get('column2Content', 300)} chars)
        
        Example: {{"title": "Gender Discrimination Impact", "column1Title": "Individual Effects", "column1Content": "Lower career advancement, reduced earning potential, decreased job satisfaction and mental health impacts", "column2Title": "Organizational Effects", "column2Content": "Reduced diversity, talent loss, legal risks, and decreased innovation and performance"}}""",

        "iconGrid": f"""Create a slide showing 8 areas affected by '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 60)} characters
        - Each category 'name': Maximum {limits.get('category_name', 25)} characters
        - Each category 'description': Maximum {limits.get('category_description', 40)} characters
        
        TITLE GUIDELINES:
        - Create a descriptive title about impact areas
        - Avoid "Target Markets" unless actually about markets
        
        Format as JSON with ONLY these fields:
        - 'title': Descriptive title (under {limits.get('title', 60)} chars)
        - 'categories': Array of exactly 8 objects, each with:
          - 'name': SHORT area name (under {limits.get('category_name', 25)} chars)
          - 'description': Brief description (under {limits.get('category_description', 40)} chars)
        
        Example: {{"title": "Gender Discrimination Impact Areas", "categories": [{{"name": "Workplace", "description": "Hiring, promotion, and pay disparities in employment"}}, {{"name": "Education", "description": "Unequal opportunities in academic and research fields"}}, {{"name": "Healthcare", "description": "Gender bias in medical treatment and research"}}, {{"name": "Technology", "description": "Underrepresentation in STEM careers and leadership"}}, {{"name": "Politics", "description": "Limited representation in government positions"}}, {{"name": "Sports", "description": "Unequal pay and media coverage in athletics"}}, {{"name": "Finance", "description": "Investment and credit discrimination issues"}}, {{"name": "Media", "description": "Stereotypical representation and coverage"}}]}}""",

        "sideBySideComparison": f"""Create a comparison slide about '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 80)} characters
        - 'leftTitle': Maximum {limits.get('leftTitle', 40)} characters
        - 'rightTitle': Maximum {limits.get('rightTitle', 40)} characters
        - Each point: Maximum {limits.get('point', 120)} characters
        
        TITLE GUIDELINES:
        - Create a balanced comparison title
        - Focus on the contrast being shown
        
        Format as JSON with ONLY these fields:
        - 'title': Comparison title (under {limits.get('title', 80)} chars)
        - 'leftTitle': Left section title (under {limits.get('leftTitle', 40)} chars)
        - 'rightTitle': Right section title (under {limits.get('rightTitle', 40)} chars)
        - 'leftPoints': Array of exactly 3 points (each under {limits.get('point', 120)} chars)
        - 'rightPoints': Array of exactly 3 points (each under {limits.get('point', 120)} chars)
        
        Example: {{"title": "Gender Discrimination: Problems vs Solutions", "leftTitle": "Current Problems", "rightTitle": "Effective Solutions", "leftPoints": ["Persistent wage gaps across industries", "Limited representation in leadership roles", "Workplace harassment and bias"], "rightPoints": ["Transparent salary bands and regular audits", "Mentorship and leadership development programs", "Strong anti-harassment policies and training"]}}""",

        "timeline": f"""Create a RECENT timeline about '{escaped_topic}'.{slide_context}
        
        CRITICAL REQUIREMENT: Focus on RECENT developments, trends, and milestones from 2015-2025. DO NOT include events from the 1990s or earlier decades unless absolutely necessary for context.
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 60)} characters
        - Each event 'title': Maximum {limits.get('event_title', 40)} characters
        - Each event 'description': Maximum {limits.get('event_description', 100)} characters
        
        TIMELINE FOCUS REQUIREMENTS:
        - Prioritize events from 2020-2025 (most recent 5 years)
        - Include developments from 2015-2019 only if highly relevant
        - Focus on current trends, recent policy changes, modern developments
        - Include future projections or upcoming milestones where appropriate
        - Use "Present" or "2024-2025" for current ongoing developments
        - DONT GIVE PRESENT KEYWORD
        
        TITLE GUIDELINES:
        - Create a modern, current timeline title
        - Use phrases like "Recent Developments", "Modern Progress", "Current Trends"
        - Avoid generic "History of" or "Evolution of" unless specifically about recent evolution
        
        Format as JSON with ONLY these fields:
        - 'title': Modern timeline title (under {limits.get('title', 60)} chars)
        - 'events': Array of 4-5 objects, each with:
          - 'year': Recent year or period (e.g., '2020', '2023', '2024-2025', 'Present')
          - 'title': Event title (under {limits.get('event_title', 40)} chars)
          - 'description': Event description (under {limits.get('event_description', 100)} chars)
        
        EXAMPLE FOR GENDER DISCRIMINATION:
        {{"title": "Recent Gender Equality Progress", "events": [{{"year": "2020", "title": "Remote Work Impact", "description": "COVID-19 highlighted gender disparities in work-life balance and caregiving"}}, {{"year": "2021", "title": "Pay Transparency Laws", "description": "Multiple states enacted salary disclosure requirements"}}, {{"year": "2022", "title": "ESG Focus", "description": "Companies prioritized diversity metrics for investment ratings"}}, {{"year": "2023", "title": "AI Bias Awareness", "description": "Growing recognition of algorithmic bias in hiring processes"}}, {{"year": "2024-2025", "title": "Ongoing Initiatives", "description": "Continued push for board diversity and inclusive leadership"}}]}}
        
        ALTERNATIVE EXAMPLE FOR TECHNOLOGY TOPIC:
        {{"title": "AI Development Milestones", "events": [{{"year": "2020", "title": "GPT-3 Launch", "description": "OpenAI released breakthrough language model"}}, {{"year": "2022", "title": "ChatGPT Release", "description": "Public access to conversational AI sparked global adoption"}}, {{"year": "2023", "title": "Enterprise Integration", "description": "Major corporations integrated AI into business operations"}}, {{"year": "2024", "title": "Regulation Framework", "description": "Governments began implementing AI governance policies"}}, {{"year": "2025", "title": "Current Focus", "description": "Emphasis on responsible AI and ethical implementation"}}]}}""",
        
        "conclusion": f"""Create a conclusion slide about '{escaped_topic}'.{slide_context}
        
        STRICTLY FOLLOW CHARACTER LIMITS (count every character including spaces):
        - 'title': Maximum {limits.get('title', 60)} characters
        - 'summary': Maximum {limits.get('summary', 200)} characters
        - Each next step: Maximum {limits.get('next_step', 50)} characters
        
        TITLE GUIDELINES:
        - Create a forward-looking conclusion title
        - Avoid generic "Key Takeaways" or "Conclusion"
        
        Format as JSON with ONLY these fields:
        - 'title': Conclusion title (under {limits.get('title', 60)} chars)
        - 'summary': Brief summary (under {limits.get('summary', 100)} chars)
        - 'nextSteps': Array of 2-3 action items (each under {limits.get('next_step', 50)} chars)
        
        Example: {{"title": "Building Equality Together", "summary": "Addressing gender discrimination requires commitment from individuals, organizations, and society to create truly inclusive environments where everyone can thrive.", "nextSteps": ["Assess current policies for bias and discrimination", "Implement bias training and inclusive hiring practices", "Track progress with regular diversity and inclusion metrics"]}}""",
    }
    
    prompt = prompts.get(layout)
    if not prompt:
        return {"error": f"Unknown layout type: {layout}"}
    
    start_time = datetime.now()
    logger.debug(f"[{start_time}] Starting content generation for layout: {layout}, topic: {topic}")
    
    try:
        request_id = f"{layout}_{topic.replace(' ', '_').replace(':', '_').replace('/', '_')[:50]}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        request_debug_dir = os.path.join(debug_dir, request_id)
        os.makedirs(request_debug_dir, exist_ok=True)
        
        with open(os.path.join(request_debug_dir, "prompt.txt"), "w") as f:
            f.write(prompt)
        
        # Generate slide content
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b", 
                "prompt": prompt,
                "stream": False
            }
        )
        
        content_result = None
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            with open(os.path.join(request_debug_dir, "raw_response.txt"), "w") as f:
                f.write(generated_text)
            
            content_result = extract_clean_json(generated_text, layout)
            
            if content_result:
                logger.debug(f"Successfully parsed JSON")
                
                # Validate character limits
                violations = validate_character_limits(content_result, layout)
                if violations:
                    logger.warning(f"Character limit violations in {layout}: {violations}")
                    with open(os.path.join(request_debug_dir, "violations.txt"), "w") as f:
                        f.write("\n".join(violations))
                
                with open(os.path.join(request_debug_dir, "extracted_json.json"), "w") as f:
                    json.dump(content_result, f, indent=2)
                
                if slide_index is not None:
                    content_result['slide_index'] = slide_index
                    content_result['total_slides'] = total_slides
                
                # Special validation for iconGrid
                if layout == "iconGrid":
                    categories = content_result.get('categories', [])
                    if len(categories) != 8:
                        logger.warning(f"iconGrid does not have exactly 8 categories, has {len(categories)}")
                        content_result = validate_and_fix_icon_grid(content_result, topic)
                
                # Special validation for numberedFeatures
                if layout == "numberedFeatures":
                    features = content_result.get('features', [])
                    if len(features) != 4:
                        logger.warning(f"numberedFeatures does not have exactly 4 features, has {len(features)}")
                        content_result = validate_and_fix_numbered_features(content_result, topic)
            else:
                logger.warning(f"Failed to parse JSON from response for {layout}")
                content_result = format_content_fallback(layout, generated_text, topic, slide_index, total_slides)
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            content_result = {"error": f"Ollama API error: {response.status_code}"}
        
        # Generate contextual image descriptions for image layouts - NO TRUNCATION
        if content_result and isinstance(content_result, dict) and "error" not in content_result:
            if "image" in layout.lower() or layout in ["sideBySideComparison", "benefitsGrid", "numberedFeatures"]:
                try:
                    logger.debug(f"Generating detailed contextual image prompt for {layout}")
                    
                    detailed_image_prompt = create_contextual_image_prompt(layout, escaped_topic, content_result, slide_context)
                    
                    with open(os.path.join(request_debug_dir, "detailed_image_prompt.txt"), "w") as f:
                        f.write(detailed_image_prompt)
                    
                    img_response = requests.post(
                        OLLAMA_API_URL,
                        json={
                            "model": "llama3.1:8b",
                            "prompt": detailed_image_prompt,
                            "stream": False
                        }
                    )
                    
                    if img_response.status_code == 200:
                        img_result = img_response.json()
                        img_description = img_result.get("response", "").strip()
                        
                        # Remove quotes if present but NO TRUNCATION
                        if img_description.startswith('"') and img_description.endswith('"'):
                            img_description = img_description[1:-1]
                        
                        with open(os.path.join(request_debug_dir, "detailed_image_description.txt"), "w") as f:
                            f.write(img_description)
                        
                        # Optional: Validate that Ollama followed the character limit
                        if len(img_description) < 300 or len(img_description) > 1000:
                            logger.warning(f"Image description length ({len(img_description)}) outside expected range 300-1000")
                        
                        # Use the generated description if current one is placeholder or too short
                        if ('imageDescription' not in content_result or 
                            not content_result['imageDescription'] or 
                            content_result['imageDescription'] in ['Image', 'Image placeholder'] or
                            len(content_result['imageDescription']) < 50):
                            content_result["imageDescription"] = img_description
                            logger.debug(f"Added detailed contextual image description ({len(img_description)} chars): {img_description[:100]}...")
                    else:
                        logger.error(f"Detailed image prompt API error: {img_response.status_code}")
                except Exception as e:
                    logger.error(f"Failed to generate detailed contextual image prompt: {str(e)}")
        
        # Apply final cleaning (but NO truncation for imageDescription)
        content_result = clean_content_result(content_result, layout)
        
        if slide_index is not None:
            content_result['slide_index'] = slide_index
            content_result['total_slides'] = total_slides
            content_result['topic'] = topic  # Add topic for process_content_for_layout
        with open(os.path.join(request_debug_dir, "final_content.json"), "w") as f:
            json.dump(content_result, f, indent=2)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.debug(f"Content generation completed in {duration:.2f} seconds")
        
        if isinstance(content_result, dict):
            content_result['topic'] = topic
            if slide_index is not None:
                content_result['slide_index'] = slide_index
                content_result['total_slides'] = total_slides
        
        return content_result
        
    except Exception as e:
        logger.exception(f"Error in generate_content: {str(e)}")
        return {"error": f"Error connecting to Ollama: {str(e)}"}

# Add these THREE missing functions to ollama_client.py:

def get_slide_context(slide_index, total_slides):
    """Get context for slide based on position"""
    if slide_index == 1:
        return "title and introduction"
    elif slide_index == total_slides:
        return "conclusion and key takeaways"
    else:
        roles = ["overview", "key benefits", "challenges", "solutions", "examples"]
        return roles[(slide_index - 2) % len(roles)]

def get_layout_specific_prompt(layout):
    """Get specific instructions for each layout type"""
    prompts = {
        'titleOnly': """
Format as JSON: {"title": "Main title", "subtitle": "Descriptive subtitle"}
Extract a compelling title and subtitle from the source content.""",
        
        'titleAndBullets': """
Format as JSON: {"title": "Slide title", "bullets": ["Point 1", "Point 2", "Point 3"]}
Extract 3-5 key points from the source content as bullet points.""",
        
        'quote': """
Format as JSON: {"quote": "Relevant quote from content", "author": "Source or author"}
Find a meaningful quote or key statement from the source content.""",
        
        'imageAndParagraph': """
Format as JSON: {"title": "Title", "imageDescription": "Image description", "paragraph": "Main paragraph"}
Extract a main point and create a descriptive paragraph from the source content.""",
        
        'twoColumn': """
Format as JSON: {"title": "Title", "column1Title": "Left title", "column1Content": "Left content", "column2Title": "Right title", "column2Content": "Right content"}
Split the source content into two related aspects or sections.""",
        
        'imageWithFeatures': """
Format as JSON: {"title": "Title", "imageDescription": "Image description", "features": [{"title": "Feature 1", "description": "Description"}, {"title": "Feature 2", "description": "Description"}]}
Extract key features or points from the source content.""",
        
        'numberedFeatures': """
Format as JSON: {"title": "Title", "imageDescription": "Image description", "features": [{"number": "1", "title": "Feature 1", "description": "Description"}]}
Extract numbered points from the source content.""",
        
        'benefitsGrid': """
Format as JSON: {"title": "Title", "imageDescription": "Image description", "benefits": [{"title": "Benefit 1", "description": "Description"}]}
Extract benefits or advantages from the source content.""",
        
        'iconGrid': """
Format as JSON: {"title": "Title", "categories": [{"name": "Category 1", "description": "Description"}]}
Extract 8 categories or areas from the source content.""",
        
        'sideBySideComparison': """
Format as JSON: {"title": "Title", "leftTitle": "Left title", "rightTitle": "Right title", "leftPoints": ["Point 1"], "rightPoints": ["Point 1"]}
Compare two aspects from the source content.""",
        
        'timeline': """
Format as JSON: {"title": "Title", "events": [{"year": "Year", "title": "Event", "description": "Description"}]}
Extract chronological events or milestones from the source content.""",
        
        'conclusion': """
Format as JSON: {"title": "Conclusion title", "summary": "Brief summary", "nextSteps": ["Step 1", "Step 2", "Step 3"]}
Summarize the main points and suggest actionable next steps."""
    }
    
    return prompts.get(layout, 'Format as appropriate JSON for the layout.')

# def generate_content_from_text(layout, topic, source_text, slide_index, total_slides, processing_mode='preserve'):

def calculate_optimal_slide_count(full_text, content_analysis):
    """Calculate optimal slide count based on actual content"""
    if not full_text:
        return 3
    
    word_count = content_analysis.get('words', len(full_text.split()))
    paragraph_count = content_analysis.get('paragraphs', len([p for p in full_text.split('\n\n') if p.strip()]))
    
    # More conservative slide count for better content preservation
    if word_count < 150:
        return 3  # Title + 1 content + conclusion
    elif word_count < 300:
        return 4  # Title + 2 content + conclusion  
    elif word_count < 500:
        return 5  # Title + 3 content + conclusion
    elif word_count < 800:
        return 6  # Title + 4 content + conclusion
    else:
        # For longer documents, be more conservative
        return min(7, max(5, word_count // 200))  # Max 7 slides
    

def extract_content_directly_from_text(layout, topic, source_text, slide_index, total_slides):
    """Directly extract content from text without AI generation as ultimate fallback"""
    
    lines = [line.strip() for line in source_text.split('\n') if line.strip()]
    paragraphs = [p.strip() for p in source_text.split('\n\n') if p.strip()]
    
    # Find sentences that might be titles
    potential_titles = []
    for line in lines[:10]:  # Check first 10 lines
        if len(line) < 100 and not line.endswith('.') and len(line.split()) < 15:
            potential_titles.append(line)
    
    main_title = potential_titles[0] if potential_titles else topic
    
    if layout == 'titleOnly':
        return {
            'title': main_title,
            'subtitle': 'Meeting Summary and Key Points'
        }
    
    elif layout == 'titleAndBullets':
        bullets = []
        # Look for bullet points or numbered items
        for line in lines:
            if (line.startswith('•') or line.startswith('-') or 
                line.startswith('*') or re.match(r'^\d+\.', line)):
                cleaned = re.sub(r'^[•\-*\d\.]\s*', '', line)
                if cleaned and len(cleaned) > 10:
                    bullets.append(cleaned)
        
        # If no explicit bullets, take first few meaningful sentences
        if not bullets:
            sentences = re.split(r'[.!?]+', source_text)
            bullets = [s.strip() for s in sentences[1:6] if len(s.strip()) > 20][:5]
        
        return {
            'title': main_title,
            'bullets': bullets[:5]  # Limit to 5 bullets
        }
    
    elif layout == 'imageAndParagraph':
        # Take the first substantial paragraph
        main_paragraph = ''
        for p in paragraphs:
            if len(p) > 100:  # Substantial paragraph
                main_paragraph = p
                break
        
        if not main_paragraph and paragraphs:
            main_paragraph = paragraphs[0]
        
        return {
            'title': main_title,
            'imageDescription': 'Meeting documentation and key discussion points',
            'paragraph': main_paragraph or 'Key meeting content and discussion points.'
        }
    
    elif layout == 'conclusion':
        # Look for conclusion keywords
        conclusion_text = ''
        next_steps = []
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['conclusion', 'summary', 'next steps', 'action items', 'follow up']):
                # Take this line and a few following lines
                conclusion_text = ' '.join(lines[i:i+3])
                break
        
        # Look for action items
        for line in lines:
            if any(keyword in line.lower() for keyword in ['action:', 'todo:', 'follow up:', 'next:']):
                cleaned = re.sub(r'^[^:]*:\s*', '', line)
                if cleaned:
                    next_steps.append(cleaned)
        
        if not next_steps:
            # Take last few lines as next steps
            next_steps = [line for line in lines[-3:] if len(line) > 10]
        
        return {
            'title': 'Meeting Summary',
            'summary': conclusion_text or 'Key outcomes and decisions from the meeting discussion.',
            'nextSteps': next_steps[:3]
        }
    
    # Default fallback for other layouts
    return {
        'title': main_title,
        'content': paragraphs[0] if paragraphs else 'Content extracted from meeting document.'
    }


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

def format_content_fallback(layout, text, topic, slide_index=None, total_slides=None):
    """Fallback formatting if JSON parsing fails"""
    logger.debug(f"Using fallback formatting for layout: {layout}")
    
    # Create slide-specific context for differentiation
    slide_context = ""
    if slide_index is not None and total_slides is not None:
        if slide_index == 2:
            slide_context = "Overview"
        elif slide_index == total_slides:
            slide_context = "Conclusion"
        else:
            aspects = [
                "Key Aspects", "Important Facts", "Applications", 
                "Examples", "Data Points", "Background",
                "Trends", "Implementation"
            ]
            slide_context = aspects[(slide_index - 3) % len(aspects)]
    
    # Create fallback content with clean titles
    if layout == "titleAndBullets":
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else f"{topic} {slide_context}"
        bullets = []
        for line in lines[1:5]:
            if line.startswith('- '):
                bullets.append(line[2:])
            elif line.startswith('* '):
                bullets.append(line[2:])
            else:
                bullets.append(line)
        
        if not bullets:
            bullets = [
                f"Important aspect of {topic}",
                f"Key consideration for {topic}",
                f"Significant impact of {topic}",
                f"Critical factor in {topic}"
            ]
            
        return {"title": clean_title(title), "bullets": bullets}
    
    elif layout == "quote":
        parts = text.split(' - ')
        quote = parts[0].strip('"')
        author = parts[1] if len(parts) > 1 else "Expert"
        return {"quote": quote, "author": author}
    
    elif layout == "imageAndParagraph":
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else f"{topic} Overview"
        paragraph = " ".join(lines[1:]) if len(lines) > 1 else f"This slide presents important information about {topic}."
        return {
            "title": clean_title(title),
            "imageDescription": f"Professional image related to {topic}",
            "paragraph": paragraph
        }
    
    elif layout == "titleOnly":
        return {
            "title": clean_title(topic),
            "subtitle": f"Understanding and Addressing the Challenge"
        }
    
    elif layout == "numberedFeatures":
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else f"{topic} Key Points"
        features = []
        
        # Try to extract features from text
        for i, line in enumerate(lines[1:5], 1):
            feature = {"number": str(i)}
            
            # Try to split into title and description
            parts = line.split(':', 1)
            if len(parts) > 1:
                feature["title"] = clean_title(parts[0])
                feature["description"] = parts[1].strip()
            else:
                feature["title"] = f"Key Point {i}"
                feature["description"] = line.strip()
            
            features.append(feature)
        
        # Ensure we have exactly 4 features
        while len(features) < 4:
            i = len(features) + 1
            features.append({
                "number": str(i),
                "title": f"Key Point {i}",
                "description": f"Important aspect of {topic}"
            })
        
        return {
            "title": clean_title(title),
            "imageDescription": f"Visual representation of {topic}",
            "features": features[:4]  # Limit to exactly 4 features
        }
    
    # Add other fallback cases as needed...
    
    logger.warning(f"No specific fallback for layout: {layout}")
    return {"error": "Could not format content"}


def generate_content_from_extracted_text(layout, topic, extracted_text, slide_index=None, total_slides=None):
    """
    Generate slide content using extracted text as the primary source
    This function creates more relevant slides by using the actual document content
    """
    
    # Limit the text to prevent overwhelming the AI (use relevant portion)
    max_text_length = 1500
    if len(extracted_text) > max_text_length:
        # Try to get the most relevant portion
        text_portions = extracted_text.split('\n\n')
        
        # If we have multiple paragraphs, select the most relevant ones
        if len(text_portions) > 1 and slide_index and total_slides:
            portion_per_slide = len(text_portions) // max(1, total_slides - 2)
            start_idx = max(0, (slide_index - 2) * portion_per_slide)
            end_idx = min(len(text_portions), start_idx + portion_per_slide + 1)
            relevant_text = '\n\n'.join(text_portions[start_idx:end_idx])
            
            # If still too long, truncate
            if len(relevant_text) > max_text_length:
                relevant_text = relevant_text[:max_text_length] + "..."
        else:
            relevant_text = extracted_text[:max_text_length] + "..."
    else:
        relevant_text = extracted_text

    slide_context = ""
    if slide_index and total_slides:
        slide_context = f" This is slide {slide_index} of {total_slides}."
        if slide_index == 1:
            slide_context += " Focus on introducing the topic."
        elif slide_index == total_slides:
            slide_context += " Focus on conclusions and next steps."
        else:
            slide_context += f" Focus on key details from the content."

    # Create layout-specific prompts that use the extracted text
    layout_prompts = {
        "titleOnly": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Create a title slide. Extract the main topic and create an engaging subtitle.{slide_context}

Return ONLY valid JSON:
{{"title": "Main title from content", "subtitle": "Descriptive subtitle"}}""",

        "titleAndBullets": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Extract 3-5 key points from the content above and format them as bullet points.{slide_context}

Return ONLY valid JSON:
{{"title": "Title based on content", "bullets": ["Point 1", "Point 2", "Point 3", "Point 4"]}}""",

        "quote": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Find a meaningful quote, key statement, or important excerpt from the content above.{slide_context}

Return ONLY valid JSON:
{{"quote": "Key quote or statement from content", "author": "Source or context"}}""",

        "imageAndParagraph": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Extract key information and create a descriptive paragraph from the content above.{slide_context}

Return ONLY valid JSON:
{{"title": "Title from content", "imageDescription": "Relevant image description", "paragraph": "Key paragraph from content"}}""",

        "twoColumn": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Split the key information from the content above into two related sections or compare two aspects.{slide_context}

Return ONLY valid JSON:
{{"title": "Title from content", "column1Title": "First aspect", "column1Content": "Content for first column", "column2Title": "Second aspect", "column2Content": "Content for second column"}}""",

        "conclusion": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Summarize the main points from the content above and suggest actionable next steps.{slide_context}

Return ONLY valid JSON:
{{"title": "Conclusion title", "summary": "Summary of key points", "nextSteps": ["Action 1", "Action 2", "Action 3"]}}""",

        "timeline": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Extract chronological events, milestones, or steps from the content above. Focus on recent developments (2015-2025).{slide_context}

Return ONLY valid JSON:
{{"title": "Timeline title", "events": [{{"year": "2020", "title": "Event", "description": "Description"}}, {{"year": "2023", "title": "Event", "description": "Description"}}]}}""",

        "imageWithFeatures": f"""Based on this extracted content about '{topic}':

CONTENT:
{relevant_text}

Extract 4 key features, benefits, or points from the content above.{slide_context}

Return ONLY valid JSON:
{{"title": "Title from content", "imageDescription": "Relevant image", "features": [{{"title": "Feature 1", "description": "Description"}}, {{"title": "Feature 2", "description": "Description"}}]}}"""
    }

    prompt = layout_prompts.get(layout, f"""Based on the extracted content about '{topic}', create appropriate content for a {layout} slide. Use the actual content provided and return valid JSON only.""")

    try:
        logger.debug(f"Generating {layout} content from extracted text (length: {len(relevant_text)})")
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            # Extract JSON from response
            content_result = extract_clean_json(generated_text, layout)
            
            if content_result:
                logger.debug(f"Successfully generated {layout} content from extracted text")
                
                # Process and validate the content
                processed_content = process_content_for_layout(content_result, layout)
                
                # Add slide tracking info
                if slide_index is not None:
                    processed_content['slide_index'] = slide_index
                    processed_content['total_slides'] = total_slides
                
                return processed_content
            else:
                logger.warning(f"Failed to parse JSON from extracted text generation for {layout}")
        else:
            logger.error(f"Ollama API error for extracted text: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error generating content from extracted text: {e}")
    
    # Fallback to regular generation if extraction-based generation fails
    logger.info(f"Falling back to regular generation for {layout}")
    return generate_content(layout, topic, slide_index, total_slides)



def generate_conclusion_from_text(conclusion_text, topic):
    """Generate conclusion content from processed text"""
    return {
        'title': 'Key Takeaways',
        'summary': conclusion_text[:200] if conclusion_text else f'Summary of key insights about {topic}',
        'nextSteps': [
            'Review the main points',
            'Apply the insights',
            'Follow up on action items'
        ]
    }

def generate_slide_content_from_processed_text(layout, topic, section_text, slide_number, total_slides):
    """Generate slide content from a section of processed text"""
    
    if layout == 'titleAndBullets':
        # Extract bullet points from the section
        sentences = [s.strip() for s in section_text.split('.') if len(s.strip()) > 20]
        bullets = sentences[:5] if sentences else ['Key point from processed content']
        
        return {
            'title': f'Key Points - Section {slide_number - 1}',
            'bullets': bullets
        }
    
    elif layout == 'imageAndParagraph':
        return {
            'title': f'Section {slide_number - 1}',
            'imageDescription': f'Visual representation of {topic}',
            'paragraph': section_text[:400] if section_text else 'Content from processed document'
        }
    
    elif layout == 'twoColumn':
        # Split section into two parts
        mid_point = len(section_text) // 2
        return {
            'title': f'Analysis - Section {slide_number - 1}',
            'column1Title': 'First Part',
            'column1Content': section_text[:mid_point],
            'column2Title': 'Second Part', 
            'column2Content': section_text[mid_point:]
        }
    
    # Default fallback
    return {
        'title': f'Content - Section {slide_number - 1}',
        'content': section_text[:200] if section_text else 'Processed content'
    }


def extract_key_value_pairs(text, context):
    """Last resort: manually extract key-value pairs from malformed JSON"""
    
    result = {}
    
    # Look for title patterns
    title_match = re.search(r'"title"[:\s]*"([^"]*)"', text)
    if title_match:
        result['title'] = title_match.group(1)
    
    # Look for bullet patterns
    bullets_match = re.search(r'"bullets"[:\s]*\[(.*?)\]', text, re.DOTALL)
    if bullets_match:
        bullets_text = bullets_match.group(1)
        bullets = re.findall(r'"([^"]*)"', bullets_text)
        result['bullets'] = bullets
    
    # Look for other common fields
    for field in ['subtitle', 'quote', 'author', 'paragraph', 'summary']:
        field_match = re.search(rf'"{field}"[:\s]*"([^"]*)"', text)
        if field_match:
            result[field] = field_match.group(1)
    
    if result:
        logger.info(f"Salvaged partial content for context {context}: {list(result.keys())}")
        return result
    
    return None


# Fixed document analysis function in ollama_client.py

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

# Fixed validation function with proper type checking

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


# Also fix the generate_slide_with_retry function to ensure proper parameter passing
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
    return generate_intelligent_fallback(layout, relevant_text, slide_plan, processing_mode)

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


def generate_intelligent_fallback(layout, relevant_text, slide_plan, processing_mode):
    """
    Generate intelligent fallback content when AI generation fails
    """
    logger.info(f"Generating intelligent fallback for {layout}")
    
    purpose = slide_plan.get('purpose', 'Content')
    content_focus = slide_plan.get('content_focus', '')
    
    # Extract meaningful content from the text
    lines = [line.strip() for line in relevant_text.split('\n') if line.strip() and len(line.strip()) > 10]
    paragraphs = [p.strip() for p in relevant_text.split('\n\n') if p.strip() and len(p.strip()) > 20]
    sentences = [s.strip() for s in re.split(r'[.!?]+', relevant_text) if len(s.strip()) > 15]
    
    if layout == 'titleOnly':
        # Use first meaningful line or purpose as title
        title = lines[0] if lines and len(lines[0]) < 80 else purpose
        subtitle = content_focus or "Key insights and analysis from the document"
        
        return {
            'title': title[:60],
            'subtitle': subtitle[:120]
        }
    
    elif layout == 'titleAndBullets':
        title = lines[0] if lines and len(lines[0]) < 80 else purpose
        
        # Extract bullets from text
        bullets = []
        
        # Try to find existing bullet points
        for line in lines:
            if line.startswith(('•', '-', '*')) or re.match(r'^\d+\.', line):
                clean_bullet = re.sub(r'^[•\-*\d\.]\s*', '', line).strip()
                if 15 <= len(clean_bullet) <= 150:
                    bullets.append(clean_bullet)
        
        # If no bullets found, create from sentences
        if len(bullets) < 3:
            bullets = []
            for sentence in sentences:
                if 15 <= len(sentence) <= 150:
                    bullets.append(sentence)
                if len(bullets) >= 5:
                    break
        
        # Ensure minimum bullets
        while len(bullets) < 3:
            bullets.append(f"Key point from the document content")
        
        return {
            'title': title[:80],
            'bullets': bullets[:5]
        }
    
    elif layout == 'imageAndParagraph':
        title = lines[0] if lines and len(lines[0]) < 80 else purpose
        
        # Find best paragraph
        paragraph = ""
        for p in paragraphs:
            if 50 <= len(p) <= 400:
                paragraph = p
                break
        
        if not paragraph and sentences:
            # Create paragraph from sentences
            paragraph = '. '.join(sentences[:3]) + '.'
        
        if not paragraph:
            paragraph = relevant_text[:400] if relevant_text else "Key information extracted from the document."
        
        return {
            'title': title[:80],
            'imageDescription': f"Visual representation related to {title.lower()}",
            'paragraph': paragraph[:400]
        }
    
    elif layout == 'conclusion':
        # Extract conclusion from end of text
        conclusion_text = relevant_text[-500:] if len(relevant_text) > 500 else relevant_text
        
        return {
            'title': 'Key Takeaways',
            'summary': conclusion_text[:200] if conclusion_text else 'Summary of main findings from the document',
            'nextSteps': [
                'Review key findings',
                'Implement recommendations',
                'Monitor progress'
            ]
        }
    
    elif layout == 'quote':
        # Find a good quote from the text
        quote = ""
        for sentence in sentences:
            if 20 <= len(sentence) <= 200:
                quote = sentence
                break
        
        if not quote:
            quote = relevant_text[:200] if relevant_text else "Key insight from the document"
        
        return {
            'quote': quote[:200],
            'author': 'Document Source'
        }
    
    elif layout == 'twoColumn':
        title = lines[0] if lines and len(lines[0]) < 80 else purpose
        
        # Split content into two parts
        mid_point = len(paragraphs) // 2 if paragraphs else 0
        
        col1_content = '\n'.join(paragraphs[:mid_point]) if mid_point > 0 else relevant_text[:300]
        col2_content = '\n'.join(paragraphs[mid_point:]) if mid_point > 0 else relevant_text[300:600]
        
        return {
            'title': title[:80],
            'column1Title': 'Key Points',
            'column1Content': col1_content[:300],
            'column2Title': 'Additional Details', 
            'column2Content': col2_content[:300]
        }
    
    # Default fallback
    return {
        'title': purpose[:80] if purpose else 'Document Content',
        'content': relevant_text[:200] if relevant_text else 'Content from document'
    }


# Update the main slide generation function
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



def validate_slide_content_quality(content, layout):
    """Enhanced validation for document-based content"""
    
    if not isinstance(content, dict):
        return False
    
    # Check for generic/placeholder content
    generic_indicators = [
        'placeholder', 'example content', 'lorem ipsum', 
        'insert here', 'content goes here', 'sample text',
        'section 1', 'section 2', 'point 1', 'point 2'
    ]
    
    content_str = str(content).lower()
    for indicator in generic_indicators:
        if indicator in content_str:
            return False
    
    # Layout-specific validation
    if layout == 'titleAndBullets':
        bullets = content.get('bullets', [])
        return (len(bullets) >= 3 and 
                all(len(str(bullet)) > 15 for bullet in bullets[:3]) and
                content.get('title') and len(content.get('title', '')) > 5)
    
    elif layout == 'imageAndParagraph':
        paragraph = content.get('paragraph', '')
        return (len(paragraph) > 50 and 
                content.get('title') and len(content.get('title', '')) > 5)
    
    elif layout == 'conclusion':
        return (content.get('summary') and len(content.get('summary', '')) > 20 and
                content.get('nextSteps') and len(content.get('nextSteps', [])) >= 2)
    
    return True


def extract_content_directly_from_section(layout, relevant_text, purpose, processing_mode):
    """Direct extraction fallback when AI generation fails"""
    
    if not relevant_text:
        return generate_fallback_content(layout, purpose, 1)
    
    lines = [line.strip() for line in relevant_text.split('\n') if line.strip()]
    paragraphs = [p.strip() for p in relevant_text.split('\n\n') if p.strip()]
    
    if layout == 'titleAndBullets':
        # Extract title from first meaningful line
        title = lines[0] if lines else purpose
        
        # Extract bullet points
        bullets = []
        for line in lines[1:]:
            if len(line) > 20 and len(line) < 200:
                bullets.append(line)
                if len(bullets) >= 5:
                    break
        
        if len(bullets) < 3:
            # Create bullets from sentences
            sentences = [s.strip() for s in relevant_text.split('.') if len(s.strip()) > 20]
            bullets = sentences[:5]
        
        return {
            'title': title[:80],  # Limit title length
            'bullets': bullets[:5]
        }
    
    elif layout == 'imageAndParagraph':
        title = lines[0] if lines else purpose
        paragraph = paragraphs[0] if paragraphs else relevant_text[:400]
        
        return {
            'title': title[:80],
            'imageDescription': f"Visual representation of {title.lower()}",
            'paragraph': paragraph[:400]
        }
    
    elif layout == 'conclusion':
        return {
            'title': 'Key Takeaways',
            'summary': relevant_text[:200],
            'nextSteps': [
                'Review the main findings',
                'Implement key recommendations', 
                'Monitor progress and outcomes'
            ]
        }
    
    # Default fallback
    return generate_fallback_content(layout, purpose, 1)


# Update the main generation function
def generate_slides_from_full_document(full_text, topic, template_id, processing_mode='preserve'):
    """
    Main function to generate slides from full document using enhanced approach
    """
    
    logger.info(f"Starting full document slide generation in {processing_mode} mode")
    
    # Stage 1: Analyze full document
    document_analysis = process_full_document_for_presentation(full_text, topic, processing_mode)
    
    if not document_analysis['success']:
        logger.warning("Document analysis failed, using fallback approach")
    
    analysis_data = document_analysis['analysis']
    slide_structure = analysis_data['presentation_plan']['slide_structure']
    
    # Stage 2: Generate slides based on analysis
    slides = []
    
    for slide_plan in slide_structure:
        try:
            content = generate_slide_from_document_section(
                slide_plan=slide_plan,
                full_document=full_text,
                document_analysis=analysis_data,
                processing_mode=processing_mode
            )
            
            if content:
                slides.append({
                    'layout': slide_plan['layout'],
                    'content': content
                })
                logger.info(f"Generated slide {slide_plan['slide_number']}: {slide_plan['layout']}")
            
        except Exception as e:
            logger.error(f"Failed to generate slide {slide_plan['slide_number']}: {e}")
            continue
    
    # Ensure minimum slide count
    if len(slides) < 3:
        logger.warning("Too few slides generated, adding fallback slides")
        while len(slides) < 3:
            fallback_slide = {
                'layout': 'titleAndBullets',
                'content': generate_fallback_content('titleAndBullets', topic, len(slides) + 1)
            }
            slides.append(fallback_slide)
    
    logger.info(f"Successfully generated {len(slides)} slides from document")
    
    return {
        'slides': slides,
        'template': template_id,
        'processing_mode': processing_mode,
        'document_analysis': analysis_data,
        'slide_count': len(slides)
    }



