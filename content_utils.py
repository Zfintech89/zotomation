def process_content_for_layout(content, layout):
    """Process content based on layout with preservation mode awareness (no truncation)"""
    # Make sure we're working with a dictionary
    if not isinstance(content, dict):
        content = {}
    
    processed = dict(content)
    processing_mode = processed.get('processing_mode', 'generate')
    
    # If in preserve mode, be more conservative with fallback content
    use_minimal_fallbacks = (processing_mode == 'preserve')
    
    # Get slide index if available for better differentiation
    slide_index = content.get('slide_index')
    total_slides = content.get('total_slides')
    
    # Generate slide-specific context for default content
    slide_context = ""
    if slide_index is not None and total_slides is not None:
        if slide_index == 2:
            slide_context = "Key Points" if use_minimal_fallbacks else "Overview"
        elif slide_index == total_slides:
            slide_context = "Summary" if use_minimal_fallbacks else "Conclusion"
        else:
            # For middle slides, use different aspects
            if use_minimal_fallbacks:
                aspects = ["Main Points", "Important Details", "Key Information", "Core Concepts"]
            else:
                aspects = ["Benefits", "Challenges", "Applications", "Examples", "Statistics", "History", "Trends", "Implementation"]
            slide_context = aspects[(slide_index - 3) % len(aspects)]
    
    if layout == 'titleAndBullets':
        # Validate existence of title - no truncation
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document: {content.get('topic', 'Key Information')}"
            else:
                processed['title'] = f"Key {slide_context or 'Points'} about {content.get('topic', 'Topic')}"
        
        # Validate bullets existence but don't truncate
        if 'bullets' not in processed or not processed['bullets']:
            if use_minimal_fallbacks:
                processed['bullets'] = [
                    "First key point from document",
                    "Second important detail",
                    "Third significant finding"
                ]
            else:
                processed['bullets'] = [
                    f"First point about {slide_context or 'important aspect'}",
                    f"Second point with specific details",
                    f"Third point with additional information",
                    f"Final consideration for this slide"
                ]
    
    elif layout == 'quote':
        if 'quote' not in processed or not processed['quote']:
            if use_minimal_fallbacks:
                processed['quote'] = f"Key insight from the document about {content.get('topic', 'this subject')}."
            else:
                processed['quote'] = f"Understanding {content.get('topic', 'this subject')} is essential for success."
        if 'author' not in processed or not processed['author']:
            if use_minimal_fallbacks:
                processed['author'] = "Document Source"
            else:
                processed['author'] = f"Expert on {content.get('topic', 'This Subject')}"
    
    elif layout == 'imageAndParagraph':
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"{content.get('topic', 'Document Content')}"
            else:
                processed['title'] = f"{slide_context or 'Key Aspects'} of {content.get('topic', 'Topic')}"
        
        if 'imageDescription' not in processed or not processed['imageDescription']:
            if use_minimal_fallbacks:
                processed['imageDescription'] = f"Visual representation of {content.get('topic', 'the content')}"
            else:
                processed['imageDescription'] = f"Professional image related to {content.get('topic', 'the topic')}"
            
        if 'paragraph' not in processed or not processed['paragraph']:
            if use_minimal_fallbacks:
                processed['paragraph'] = f"This section presents important information from the document about {content.get('topic', 'the topic')}."
            else:
                processed['paragraph'] = f"This slide explores the {slide_context or 'important aspects'} of {content.get('topic', 'this topic')}."
    
    elif layout == 'twoColumn':
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"{content.get('topic', 'Document Analysis')}"
            else:
                processed['title'] = f"{slide_context or 'Comparing Aspects'} of {content.get('topic', 'Topic')}"
        
        if 'column1Title' not in processed or not processed['column1Title']:
            processed['column1Title'] = "First Section" if use_minimal_fallbacks else "First Aspect"
        if 'column2Title' not in processed or not processed['column2Title']:
            processed['column2Title'] = "Second Section" if use_minimal_fallbacks else "Second Aspect"
        if 'column1Content' not in processed or not processed['column1Content']:
            if use_minimal_fallbacks:
                processed['column1Content'] = f"First section content from the document about {content.get('topic', 'the topic')}."
            else:
                processed['column1Content'] = f"Content about the first aspect of {content.get('topic', 'the topic')}."
        if 'column2Content' not in processed or not processed['column2Content']:
            if use_minimal_fallbacks:
                processed['column2Content'] = f"Second section content from the document about {content.get('topic', 'the topic')}."
            else:
                processed['column2Content'] = f"Content about the second aspect of {content.get('topic', 'the topic')}."
    
    elif layout == 'titleOnly':
        if 'title' not in processed or not processed['title']:
            processed['title'] = f"{content.get('topic', 'Document Title')}"
        if 'subtitle' not in processed or not processed['subtitle']:
            if use_minimal_fallbacks:
                processed['subtitle'] = "Document Summary and Analysis"
            else:
                processed['subtitle'] = "A comprehensive overview and analysis"
    
    elif layout == "imageWithFeatures":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"{content.get('topic', 'Document Features')}"
            else:
                processed['title'] = f"Features of {content.get('topic', 'Topic')}"
        if 'imageDescription' not in processed or not processed['imageDescription']:
            if use_minimal_fallbacks:
                processed['imageDescription'] = f"Image representing {content.get('topic', 'the content')}"
            else:
                processed['imageDescription'] = f"Image showing {content.get('topic', 'the topic')}"
        if 'features' not in processed or not processed['features']:
            if use_minimal_fallbacks:
                processed['features'] = [
                    {'title': 'Key Point 1', 'description': 'First important point from document'},
                    {'title': 'Key Point 2', 'description': 'Second important point from document'},
                    {'title': 'Key Point 3', 'description': 'Third important point from document'},
                    {'title': 'Key Point 4', 'description': 'Fourth important point from document'}
                ]
            else:
                processed['features'] = [
                    {'title': 'Feature 1', 'description': 'Description of feature 1'},
                    {'title': 'Feature 2', 'description': 'Description of feature 2'},
                    {'title': 'Feature 3', 'description': 'Description of feature 3'},
                    {'title': 'Feature 4', 'description': 'Description of feature 4'}
                ]
    
    elif layout == "numberedFeatures":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document Points: {content.get('topic', 'Topic')}"
            else:
                processed['title'] = f"Key Points about {content.get('topic', 'Topic')}"
        if 'imageDescription' not in processed or not processed['imageDescription']:
            if use_minimal_fallbacks:
                processed['imageDescription'] = f"Visual related to {content.get('topic', 'the content')}"
            else:
                processed['imageDescription'] = f"Image related to {content.get('topic', 'the topic')}"
        if 'features' not in processed or not processed['features']:
            processed['features'] = []
        
        # Ensure exactly 4 features
        while len(processed['features']) < 4:
            i = len(processed['features']) + 1
            if use_minimal_fallbacks:
                processed['features'].append({
                    'number': str(i),
                    'title': f'Point {i}',
                    'description': f'Important point {i} from document'
                })
            else:
                processed['features'].append({
                    'number': str(i),
                    'title': f'Feature {i}',
                    'description': f'Description of feature {i}'
                })
    
    elif layout == "benefitsGrid":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document Benefits: {content.get('topic', 'Topic')}"
            else:
                processed['title'] = f"Benefits of {content.get('topic', 'Topic')}"
        if 'imageDescription' not in processed or not processed['imageDescription']:
            if use_minimal_fallbacks:
                processed['imageDescription'] = f"Image showing {content.get('topic', 'the content')}"
            else:
                processed['imageDescription'] = f"Image showing benefits of {content.get('topic', 'the topic')}"
        if 'benefits' not in processed or not processed['benefits']:
            processed['benefits'] = []
        
        # Ensure exactly 4 benefits
        while len(processed['benefits']) < 4:
            i = len(processed['benefits']) + 1
            if use_minimal_fallbacks:
                processed['benefits'].append({
                    'title': f'Point {i}',
                    'description': f'Important benefit {i} from document'
                })
            else:
                processed['benefits'].append({
                    'title': f'Benefit {i}',
                    'description': f'Description of benefit {i}'
                })
    
    elif layout == "iconGrid":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document Categories: {content.get('topic', 'Topic')}"
            else:
                processed['title'] = f"Categories Related to {content.get('topic', 'Topic')}"
        if 'categories' not in processed or not processed['categories']:
            processed['categories'] = []
        
        # Ensure exactly 8 categories
        if use_minimal_fallbacks:
            default_categories = [
                {"name": "Section 1", "description": "First document section"},
                {"name": "Section 2", "description": "Second document section"},
                {"name": "Section 3", "description": "Third document section"},
                {"name": "Section 4", "description": "Fourth document section"},
                {"name": "Section 5", "description": "Fifth document section"},
                {"name": "Section 6", "description": "Sixth document section"},
                {"name": "Section 7", "description": "Seventh document section"},
                {"name": "Section 8", "description": "Eighth document section"}
            ]
        else:
            default_categories = [
                {"name": "Category 1", "description": "Description 1"},
                {"name": "Category 2", "description": "Description 2"},
                {"name": "Category 3", "description": "Description 3"},
                {"name": "Category 4", "description": "Description 4"},
                {"name": "Category 5", "description": "Description 5"},
                {"name": "Category 6", "description": "Description 6"},
                {"name": "Category 7", "description": "Description 7"},
                {"name": "Category 8", "description": "Description 8"}
            ]
        
        while len(processed['categories']) < 8:
            i = len(processed['categories'])
            processed['categories'].append(default_categories[i])
    
    elif layout == "sideBySideComparison":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document Comparison: {content.get('topic', 'Topic')}"
            else:
                processed['title'] = f"Comparing Aspects of {content.get('topic', 'Topic')}"
        if 'leftTitle' not in processed or not processed['leftTitle']:
            processed['leftTitle'] = "First Section" if use_minimal_fallbacks else "Challenges"
        if 'rightTitle' not in processed or not processed['rightTitle']:
            processed['rightTitle'] = "Second Section" if use_minimal_fallbacks else "Solutions"
        if 'leftPoints' not in processed or not processed['leftPoints']:
            if use_minimal_fallbacks:
                processed['leftPoints'] = ["First document point", "Second document point", "Third document point"]
            else:
                processed['leftPoints'] = ["Point 1", "Point 2", "Point 3"]
        if 'rightPoints' not in processed or not processed['rightPoints']:
            if use_minimal_fallbacks:
                processed['rightPoints'] = ["First related point", "Second related point", "Third related point"]
            else:
                processed['rightPoints'] = ["Point 1", "Point 2", "Point 3"]
    
    elif layout == "timeline":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document Timeline: {content.get('topic', 'Events')}"
            else:
                processed['title'] = f"Timeline of {content.get('topic', 'Events')}"
        if 'events' not in processed or not processed['events']:
            if use_minimal_fallbacks:
                processed['events'] = [
                    {'year': 'Period 1', 'title': 'First Phase', 'description': 'Initial development phase'},
                    {'year': 'Period 2', 'title': 'Second Phase', 'description': 'Implementation phase'},
                    {'year': 'Period 3', 'title': 'Current Phase', 'description': 'Current status and progress'}
                ]
            else:
                processed['events'] = [
                    {'year': '2020', 'title': 'Event 1', 'description': 'Description 1'},
                    {'year': '2022', 'title': 'Event 2', 'description': 'Description 2'},
                    {'year': '2024', 'title': 'Event 3', 'description': 'Description 3'}
                ]
    
    elif layout == "conclusion":
        if 'title' not in processed or not processed['title']:
            if use_minimal_fallbacks:
                processed['title'] = f"Document Summary: {content.get('topic', 'Presentation')}"
            else:
                processed['title'] = f"Key Takeaways from {content.get('topic', 'Presentation')}"
        if 'summary' not in processed or not processed['summary']:
            if use_minimal_fallbacks:
                processed['summary'] = f"Summary of key findings and insights from the document about {content.get('topic', 'the topic')}."
            else:
                processed['summary'] = f"Summary of key insights about {content.get('topic', 'the topic')}."
        if 'nextSteps' not in processed or not processed['nextSteps']:
            if use_minimal_fallbacks:
                processed['nextSteps'] = [
                    "Review document findings",
                    "Apply key recommendations", 
                    "Monitor implementation progress"
                ]
            else:
                processed['nextSteps'] = [
                    "Implement key insights",
                    "Schedule follow-up discussions", 
                    "Monitor progress and metrics"
                ]

    # Clean up temporary variables
    if 'slide_index' in processed:
        del processed['slide_index']
    if 'total_slides' in processed:
        del processed['total_slides']
    if 'processing_mode' in processed:
        del processed['processing_mode']
    
    return processed