function initializeTemplates() {
    const templatesContainer = document.getElementById('templates-container');
    
    if (!templatesContainer) {
        console.error('Templates container not found');
        return;
    }
    
    // Clear any existing content
    templatesContainer.innerHTML = '';
    
    // Add each template option
    templates.forEach(template => {
        const templateCard = document.createElement('div');
        templateCard.className = 'template-card';
        templateCard.dataset.id = template.id;
        
        const templatePreview = document.createElement('div');
        templatePreview.className = `template-preview ${template.previewClass}`;
        
        const templateName = document.createElement('div');
        templateName.className = 'template-name';
        templateName.textContent = template.name;
        
        templateCard.appendChild(templatePreview);
        templateCard.appendChild(templateName);
        
        templatesContainer.appendChild(templateCard);
        
        // Add click event to select template
        templateCard.addEventListener('click', function() {
            // Remove selected class from all template cards
            document.querySelectorAll('.template-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // Add selected class to clicked template
            this.classList.add('selected');
        });
    });
    
    // Select first template by default
    const firstTemplate = document.querySelector('.template-card');
    if (firstTemplate) {
        firstTemplate.classList.add('selected');
    }
}
// In layouts.js - Remove any debugging elements
// Add this CSS to hide any debug elements
const style = document.createElement('style');
style.textContent = `
  [data-debug], .debug-info {
    display: none !important;
  }
`;
document.head.appendChild(style);
// Export the templates for use in other files
window.ppgTemplates = {
    templates,
    initializeTemplates
};

if (!window.ppgTemplates) {
    window.ppgTemplates = { templates: [] };
}


const layouts = [
    {
        id: 'titleAndBullets',
        name: 'Title and Bullets',
        description: 'A slide with a title and bullet points',
        icon: 'fa-list'
    },
    {
        id: 'quote',
        name: 'Quote',
        description: 'A slide with a quotation and attribution',
        icon: 'fa-quote-right'
    },
    {
        id: 'imageAndParagraph',
        name: 'Image and Text',
        description: 'A slide with an image and descriptive text',
        icon: 'fa-image'
    },
    {
        id: 'twoColumn',
        name: 'Two Columns',
        description: 'A slide with two columns of content',
        icon: 'fa-columns'
    },
    {
        id: 'titleOnly',
        name: 'Title Slide',
        description: 'A simple title slide',
        icon: 'fa-heading'
    },
    {
        id: 'imageWithFeatures',
        name: 'Image with Features',
        description: 'A slide with an image and feature points with icons',
        icon: 'fa-th-list'
    },
    {
        id: 'numberedFeatures',
        name: 'Numbered Features',
        description: 'A slide with numbered feature points',
        icon: 'fa-list-ol'
    },

    {
        id: 'benefitsGrid',
        name: 'Benefits Grid',
        description: 'A slide with a grid of benefits',
        icon: 'fa-th'
    },
    {
        id: 'iconGrid',
        name: 'Icon Grid',
        description: 'A slide with a grid of icons and categories',
        icon: 'fa-icons'
    },
    {
        id: 'sideBySideComparison',
        name: 'Side by Side Comparison',
        description: 'A slide comparing two concepts side by side',
        icon: 'fa-balance-scale'
    },
    {
        id: 'timeline',
        name: 'Timeline',
        description: 'A chronological timeline of events',
        icon: 'fa-history'
    },
    {
    id: 'conclusion',
    name: 'Conclusion',
    description: 'A slide summarizing key takeaways',
    icon: 'fa-check-circle'
}
];

function createTimelineForm(content) {
    const title = content.title || '';
    const events = content.events || [{}, {}, {}, {}];
    
    let eventsFields = '';
    for (let i = 0; i < events.length; i++) {
        const event = events[i] || {};
        eventsFields += createEventFields(i, event);
    }
    
    const formHtml = `
        <h3>Edit Timeline Slide</h3>
        <div class="form-group">
            <label for="title">Slide Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div id="events-container">
            ${eventsFields}
        </div>
        <div class="form-group timeline-controls">
        </div>
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">
                <i class="fas fa-save"></i> Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;

    return formHtml;
}

// This function should be called after the form is added to the DOM
function setupTimelineFormEventListeners() {
    // Get the add event button
    const addEventBtn = document.getElementById('add-event-btn');
    if (addEventBtn) {
        // Add click event listener
        addEventBtn.addEventListener('click', function() {
            const eventsContainer = document.getElementById('events-container');
            const eventCount = eventsContainer.getElementsByClassName('timeline-event-form').length;
            
            // Create a new event form
            const newEventHtml = createEventFields(eventCount, {});
            
            // Add to container
            const tempContainer = document.createElement('div');
            tempContainer.innerHTML = newEventHtml;
            eventsContainer.appendChild(tempContainer.firstElementChild);
            
            // Add animation class
            const newEventForm = eventsContainer.lastElementChild;
            newEventForm.style.animation = 'slideDown 0.3s ease-out';
            
            // Scroll to the new event
            newEventForm.scrollIntoView({ behavior: 'smooth', block: 'end' });
            
            // Show success message
            if (typeof showNotification === 'function') {
                showNotification('New event added successfully', 'success');
            }
        });
    }
}

function createEventFields(index, event) {
    return `
        <div class="timeline-event-form">
            <h4>
                <i class="fas fa-clock"></i>
                Event ${index + 1}
            </h4>
            <div class="form-group">
                <label for="event-${index}-year">Year/Period:</label>
                <input type="text" id="event-${index}-year" name="event-${index}-year" 
                       value="${escapeHTML(event.year || '')}" class="form-control"
                       placeholder="e.g., 2024 or Early 20th Century">
            </div>
            <div class="form-group">
                <label for="event-${index}-title">Event Title:</label>
                <input type="text" id="event-${index}-title" name="event-${index}-title" 
                       value="${escapeHTML(event.title || '')}" class="form-control"
                       placeholder="Enter a concise title for this event">
            </div>
            <div class="form-group">
                <label for="event-${index}-description">Description:</label>
                <textarea id="event-${index}-description" name="event-${index}-description" 
                         class="form-control" rows="3"
                         placeholder="Describe the important details of this event">${escapeHTML(event.description || '')}</textarea>
            </div>
        </div>
    `;
}

function renderPreview(layout, content, templateId) {
    const template = window.ppgTemplates.templates.find(t => t.id === templateId) || window.ppgTemplates.templates[0];
    
    switch(layout) {
        case 'titleAndBullets':
            return renderTitleAndBullets(content, template);
        case 'quote':
            return renderQuote(content, template);
        case 'imageAndParagraph':
            return renderImageAndParagraph(content, template);
        case 'twoColumn':
            return renderTwoColumn(content, template);
        case 'titleOnly':
            return renderTitleOnly(content, template);
        // New layout renderers
        case 'imageWithFeatures':
            return renderImageWithFeatures(content, template);
        case 'numberedFeatures':
            return renderNumberedFeatures(content, template);
        case 'benefitsGrid':
            return renderBenefitsGrid(content, template);
        case 'iconGrid':
            return renderIconGrid(content, template);
        case 'sideBySideComparison':
            return renderSideBySideComparison(content, template);
        case 'timeline':
            return renderTimeline(content, template);   
        case 'conclusion':
            return renderConclusion(content, template);  // Add this line 
        default:
            return `<div class="preview-error">Unknown layout type: ${layout}</div>`;
    }
}
function collectFormData(layout) {
    const formData = {};
    switch(layout) {
        case 'titleAndBullets':
            formData.title = document.getElementById('title').value;
            formData.bullets = [];
            for (let i = 0; i < 8; i++) {
                const bullet = document.getElementById(`bullet-${i}`).value;
                if (bullet.trim()) {
                    formData.bullets.push(bullet);
                }
            }
            break;
        case 'quote':
            formData.quote = document.getElementById('quote').value;
            formData.author = document.getElementById('author').value;
            break;
        case 'imageAndParagraph':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.paragraph = document.getElementById('paragraph').value;
            break;
        case 'twoColumn':
            formData.title = document.getElementById('title').value;
            formData.column1Title = document.getElementById('column1Title').value;
            formData.column1Content = document.getElementById('column1Content').value;
            formData.column2Title = document.getElementById('column2Title').value;
            formData.column2Content = document.getElementById('column2Content').value;
            break;
        case 'titleOnly':
            formData.title = document.getElementById('title').value;
            formData.subtitle = document.getElementById('subtitle').value;
            break;
        case 'imageWithFeatures':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.features = [];
            for (let i = 0; i < 4; i++) {
                const title = document.getElementById(`feature-${i}-title`).value;
                const description = document.getElementById(`feature-${i}-description`).value;
                if (title.trim() || description.trim()) {
                    formData.features.push({ title, description });
                }
            }
            break;
        case 'numberedFeatures':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.features = [];
            for (let i = 0; i < 4; i++) {
                const title = document.getElementById(`feature-${i}-title`).value;
                const description = document.getElementById(`feature-${i}-description`).value;
                if (title.trim() || description.trim()) {
                    formData.features.push({ number: i + 1, title, description });
                }
            }
            break;
        case 'pricingTable':
            formData.title = document.getElementById('title').value;
            formData.priceAmount = document.getElementById('priceAmount').value;
            formData.percentage = document.getElementById('percentage').value;
            formData.priceDescription = document.getElementById('priceDescription').value;
            formData.percentageDescription = document.getElementById('percentageDescription').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            break;
        case 'benefitsGrid':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.benefits = [];
            for (let i = 0; i < 4; i++) {
                const title = document.getElementById(`benefit-${i}-title`).value;
                const description = document.getElementById(`benefit-${i}-description`).value;
                if (title.trim() || description.trim()) {
                    formData.benefits.push({ title, description });
                }
            }
            break;
        case 'iconGrid':
            formData.title = document.getElementById('title').value;
            formData.categories = [];
            for (let i = 0; i < 8; i++) {
                const name = document.getElementById(`category-${i}-name`).value;
                const description = document.getElementById(`category-${i}-description`).value;
                if (name.trim() || description.trim()) {
                    formData.categories.push({ name, description });
                }
            }
            break;
        case 'sideBySideComparison':
            formData.title = document.getElementById('title').value;
            formData.leftTitle = document.getElementById('leftTitle').value;
            formData.rightTitle = document.getElementById('rightTitle').value;
            formData.leftPoints = [];
            for (let i = 0; i < 3; i++) {
                const point = document.getElementById(`left-point-${i}`).value;
                if (point.trim()) {
                    formData.leftPoints.push(point);
                }
            }
            formData.rightPoints = [];
            for (let i = 0; i < 3; i++) {
                const point = document.getElementById(`right-point-${i}`).value;
                if (point.trim()) {
                    formData.rightPoints.push(point);
                }
            }
            break;
    }
    return formData;
}

window.ppgLayouts = {
    layouts,
    renderPreview,
    createEditForm,
    getLayoutById,
    renderTimeline,
    renderConclusion,  // Add this
    createConclusionForm  // Add this  
};

// new respnsive layouts 

function renderTitleAndBullets(content, template) {
    const title = content.title || 'Title';
    const bullets = content.bullets || [];
    
    // Calculate dynamic font sizes based on content length
    const titleLength = title.length;
    const titleFontSize = Math.max(22, Math.min(36, 36 * (50 / Math.max(50, titleLength))));
    
    let bulletHtml = '';
    bullets.forEach(bullet => {
        // Calculate bullet font size based on length
        const bulletLength = bullet.length;
        const bulletFontSize = Math.max(16, Math.min(20, 20 * (100 / Math.max(100, bulletLength))));
        
        bulletHtml += `<li style="color: ${template.colors.text}; margin-bottom: 15px; font-size: ${bulletFontSize}px; line-height: 1.3; word-wrap: break-word;">${bullet}</li>`;
    });
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 15px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <ul style="color: ${template.colors.text}; padding-left: 40px; margin-top: 10px; overflow: visible;">
                ${bulletHtml}
            </ul>
        </div>
    `;
}

function renderQuote(content, template) {
    const quote = content.quote || 'Quote goes here';
    const author = content.author || 'Author';
    
    // Calculate dynamic font sizes based on content length
    const quoteLength = quote.length;
    const authorLength = author.length;
    
    const quoteFontSize = Math.max(20, Math.min(32, 32 * (150 / Math.max(150, quoteLength))));
    const authorFontSize = Math.max(16, Math.min(24, 24 * (30 / Math.max(30, authorLength))));
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; min-height: 400px; padding: 40px; overflow: visible;">
            <div class="quote-container" style="width: 80%; max-width: 800px; text-align: center; overflow: visible;">
                <p class="quote" style="color: ${template.colors.primary}; font-size: ${quoteFontSize}px; font-style: italic; line-height: 1.4; margin-bottom: 30px; word-wrap: break-word; white-space: normal; overflow: visible;">"${quote}"</p>
                <p class="author" style="color: ${template.colors.secondary}; font-size: ${authorFontSize}px; text-align: right; word-wrap: break-word; white-space: normal; overflow: visible;">— ${author}</p>
            </div>
        </div>
    `;
}

function renderImageAndParagraph(content, template) {
    const title = content.title || 'Title';
    const paragraph = content.paragraph || 'Paragraph text';
    const imageDescription = content.imageDescription || 'Image description';
    
    // Calculate dynamic font sizes based on content length
    const titleLength = title.length;
    const paragraphLength = paragraph.length;
    const imageDescLength = imageDescription.length;
    
    // Base sizes
    let titleFontSize = 32;
    let paragraphFontSize = 18;
    let imageDescFontSize = 14;
    
    // Reduce font size for longer content
    if (titleLength > 50) {
        titleFontSize = Math.max(20, 32 - Math.floor((titleLength - 50) / 15));
    }
    
    if (paragraphLength > 300) {
        paragraphFontSize = Math.max(14, 18 - Math.floor((paragraphLength - 300) / 200));
    }
    
    if (imageDescLength > 100) {
        imageDescFontSize = Math.max(9, 14 - Math.floor((imageDescLength - 100) / 100));
    }
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 20px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <div class="image-paragraph-container" style="display: flex; gap: 20px; align-items: flex-start; height: auto; overflow: visible;">
                <div class="image-placeholder" style="background-color: ${template.colors.secondary}; width: 40%; min-height: 200px; height: auto; display: flex; align-items: center; justify-content: center; border-radius: 8px; flex-shrink: 0; overflow: visible;">
                    <p style="color: ${template.colors.background}; text-align: center; padding: 15px; font-size: ${imageDescFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${imageDescription}</p>
                </div>
                <div class="paragraph-container" style="width: 60%; flex-grow: 1; height: auto; overflow: visible; padding: 0 10px;">
                    <p style="color: ${template.colors.text}; font-size: ${paragraphFontSize}px; line-height: 1.5; margin: 0 auto; word-wrap: break-word; white-space: normal; overflow: visible; text-overflow: unset;">
                        ${paragraph}
                    </p>
                </div>
            </div>
        </div>
    `;
}

function renderTwoColumn(content, template) {
    const title = content.title || 'Title';
    const col1Title = content.column1Title || 'Column 1';
    const col1Content = content.column1Content || 'Column 1 content';
    const col2Title = content.column2Title || 'Column 2';
    const col2Content = content.column2Content || 'Column 2 content';
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const col1TitleLength = col1Title.length;
    const col2TitleLength = col2Title.length;
    const col1ContentLength = col1Content.length;
    const col2ContentLength = col2Content.length;
    
    const titleFontSize = Math.max(20, Math.min(30, 30 * (50 / Math.max(50, titleLength))));
    const col1TitleFontSize = Math.max(16, Math.min(24, 24 * (30 / Math.max(30, col1TitleLength))));
    const col2TitleFontSize = Math.max(16, Math.min(24, 24 * (30 / Math.max(30, col2TitleLength))));
    const col1ContentFontSize = Math.max(12, Math.min(16, 16 * (200 / Math.max(200, col1ContentLength))));
    const col2ContentFontSize = Math.max(12, Math.min(16, 16 * (200 / Math.max(200, col2ContentLength))));
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 20px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <div class="two-column-container" style="display: flex; gap: 30px; align-items: flex-start; height: auto;">
                <div class="column" style="flex: 1; overflow: visible;">
                    <h2 style="color: ${template.colors.secondary}; font-size: ${col1TitleFontSize}px; margin-bottom: 10px; word-wrap: break-word; white-space: normal; overflow: visible;">${col1Title}</h2>
                    <p style="color: ${template.colors.text}; font-size: ${col1ContentFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${col1Content}</p>
                </div>
                <div class="column" style="flex: 1; overflow: visible;">
                    <h2 style="color: ${template.colors.secondary}; font-size: ${col2TitleFontSize}px; margin-bottom: 10px; word-wrap: break-word; white-space: normal; overflow: visible;">${col2Title}</h2>
                    <p style="color: ${template.colors.text}; font-size: ${col2ContentFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${col2Content}</p>
                </div>
            </div>
        </div>
    `;
}

function renderTitleOnly(content, template) {
    const title = content.title || 'Title';
    const subtitle = content.subtitle || 'Subtitle';
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const subtitleLength = subtitle.length;
    
    const titleFontSize = Math.max(32, Math.min(48, 48 * (40 / Math.max(40, titleLength))));
    const subtitleFontSize = Math.max(20, Math.min(32, 32 * (60 / Math.max(60, subtitleLength))));
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; min-height: 400px; padding: 40px; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; font-size: ${titleFontSize}px; text-align: center; margin-bottom: 30px; word-wrap: break-word; white-space: normal; overflow: visible; line-height: 1.2; max-width: 90%;">${title}</h1>
            <h2 style="color: ${template.colors.secondary}; font-size: ${subtitleFontSize}px; text-align: center; word-wrap: break-word; white-space: normal; overflow: visible; line-height: 1.3; max-width: 90%;">${subtitle}</h2>
        </div>
    `;
}

function renderImageWithFeatures(content, template) {
    const title = content.title || 'Title';
    const features = content.features || [];
    const imageDescription = content.imageDescription || 'Image';

    // Calculate dynamic font sizes
    const titleLength = title.length;
    const titleFontSize = Math.max(24, Math.min(32, 32 * (40 / Math.max(40, titleLength))));
    
    // No truncation - use content exactly as provided
    let featuresHtml = '';
    features.slice(0, 4).forEach(feature => {
        const featureTitle = feature.title || 'Feature';
        const featureDescription = feature.description || '';
        
        // Calculate dynamic font sizes for feature content
        const featureTitleLength = featureTitle.length;
        const featureDescLength = featureDescription.length;
        
        const featureTitleFontSize = Math.max(14, Math.min(17, 17 * (30 / Math.max(30, featureTitleLength))));
        const featureDescFontSize = Math.max(12, Math.min(15, 15 * (50 / Math.max(50, featureDescLength))));
        
        featuresHtml += `
            <div class="feature" style="display: flex; margin-bottom: 20px; align-items: flex-start;">
                <div class="feature-icon" style="background-color: ${template.colors.accent}; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; flex-shrink: 0;">
                    <span style="color: white; font-size: 18px;">⚙️</span>
                </div>
                <div class="feature-content" style="flex: 1; word-wrap: break-word; overflow: visible;">
                    <h3 style="color: ${template.colors.primary}; margin: 0 0 8px 0; font-size: ${featureTitleFontSize}px; font-weight: bold; line-height: 1.3; word-wrap: break-word; white-space: normal; overflow: visible;">${featureTitle}</h3>
                    <p style="color: ${template.colors.text}; margin: 0; font-size: ${featureDescFontSize}px; line-height: 1.5; word-wrap: break-word; white-space: normal; overflow: visible;">${featureDescription}</p>
                </div>
            </div>
        `;
    });

    // Calculate image description font size
    const imageDescLength = imageDescription.length;
    const imageDescFontSize = Math.max(9, Math.min(14, 14 * (100 / Math.max(100, imageDescLength))));

    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 20px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word;">${title}</h1>
            <div class="image-features-container" style="display: flex; gap: 25px; align-items: flex-start;">
                <div class="image-placeholder" style="background-color: ${template.colors.secondary}; width: 40%; min-height: 350px; display: flex; align-items: center; justify-content: center; border-radius: 8px; flex-shrink: 0;">
                    <p style="color: white; text-align: center; padding: 15px; font-size: ${imageDescFontSize}px; line-height: 1.4; word-wrap: break-word;">${imageDescription}</p>
                </div>
                <div class="features-container" style="width: 60%; flex-grow: 1; overflow: visible; max-height: none;">
                    ${featuresHtml}
                </div>
            </div>
        </div>
    `;
}

function renderNumberedFeatures(content, template) {
    // Ensure we have content object
    content = content || {};
    
    // Get title and image description
    const title = content.title || 'Title';
    const imageDescription = content.imageDescription || 'Image';
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const titleFontSize = Math.max(24, Math.min(32, 32 * (40 / Math.max(40, titleLength))));
    
    // Get features array with validation
    let features = Array.isArray(content.features) ? content.features : [];
    
    // Ensure exactly 4 features with proper structure
    if (features.length < 4) {
        const defaultFeatures = [
            {number: "1", title: "Key Feature 1", description: "Description of key feature 1"},
            {number: "2", title: "Key Feature 2", description: "Description of key feature 2"},
            {number: "3", title: "Key Feature 3", description: "Description of key feature 3"},
            {number: "4", title: "Key Feature 4", description: "Description of key feature 4"}
        ];
        features = [...features, ...defaultFeatures.slice(features.length)];
    }
    features = features.slice(0, 4); // Limit to exactly 4 features
    
    // Generate feature HTML with grid layout
    let featuresHtml = '<div class="features-grid" style="width: 100%; display: grid; grid-template-columns: repeat(2, 1fr); grid-gap: 30px; margin-top: 30px;">';
    
    features.forEach((feature, index) => {
        const number = feature.number || String(index + 1);
        const featureTitle = feature.title || `Feature ${number}`;
        const featureDesc = feature.description || 'Description';
        
        // Calculate dynamic font sizes for feature content
        const featureTitleLength = featureTitle.length;
        const featureDescLength = featureDesc.length;
        
        const featureTitleFontSize = Math.max(16, Math.min(20, 20 * (30 / Math.max(30, featureTitleLength))));
        const featureDescFontSize = Math.max(12, Math.min(16, 16 * (100 / Math.max(100, featureDescLength))));
        
        featuresHtml += `
            <div class="numbered-feature" style="display: flex; align-items: flex-start;">
                <div class="feature-number" style="background-color: ${template.colors.secondary}; width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; flex-shrink: 0;">
                    <span style="color: ${template.colors.background}; font-size: 20px; font-weight: bold;">${number}</span>
                </div>
                <div class="feature-content" style="flex: 1; overflow: visible;">
                    <h3 style="color: ${template.colors.primary}; margin: 0 0 6px 0; font-size: ${featureTitleFontSize}px; font-weight: bold; line-height: 1.3; word-wrap: break-word; white-space: normal; overflow: visible;">${featureTitle}</h3>
                    <p style="color: ${template.colors.text}; margin: 0; font-size: ${featureDescFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${featureDesc}</p>
                </div>
            </div>
        `;
    });
    
    featuresHtml += '</div>';
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 20px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            ${featuresHtml}
        </div>
    `;
}

function renderBenefitsGrid(content, template) {
    const title = content.title || 'Benefits';
    const imageDescription = content.imageDescription || "Image";
    const benefits = content.benefits || [];
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const titleFontSize = Math.max(24, Math.min(32, 32 * (40 / Math.max(40, titleLength))));
    
    // Calculate image description font size
    const imageDescLength = imageDescription.length;
    const imageDescFontSize = Math.max(9, Math.min(14, 14 * (100 / Math.max(100, imageDescLength))));
    
    // Process benefits with responsive sizing
    let benefitsHtml = '';
    
    benefits.slice(0, 4).forEach((benefit) => {
        const benefitTitle = benefit.title || '';
        const benefitDesc = benefit.description || '';
        
        // Calculate dynamic font sizes for benefit content
        const benefitTitleLength = benefitTitle.length;
        const benefitDescLength = benefitDesc.length;
        
        const benefitTitleFontSize = Math.max(12, Math.min(16, 16 * (25 / Math.max(25, benefitTitleLength))));
        const benefitDescFontSize = Math.max(10, Math.min(14, 14 * (60 / Math.max(60, benefitDescLength))));
        
        benefitsHtml += `
            <div class="benefit-card" style="background-color: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%; display: flex; flex-direction: column;">
                <div style="border-left: 4px solid ${template.colors.secondary}; padding-left: 10px; margin-bottom: 10px;">
                    <h3 style="color: ${template.colors.primary}; margin: 0 0 5px 0; font-size: ${benefitTitleFontSize}px; font-weight: bold; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">
                        ${benefitTitle}
                    </h3>
                </div>
                <p style="color: ${template.colors.text}; font-size: ${benefitDescFontSize}px; line-height: 1.3; margin: 0; flex-grow: 1; word-wrap: break-word; white-space: normal; overflow: visible;">
                    ${benefitDesc}
                </p>
            </div>
        `;
    });
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 30px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <div class="benefits-container" style="display: flex; gap: 30px; align-items: flex-start;">
                <div class="image-placeholder" style="background-color: ${template.colors.secondary}; width: 40%; height: auto; min-height: 300px; display: flex; align-items: center; justify-content: center; border-radius: 8px; flex-shrink: 0;">
                    <p style="color: white; text-align: center; padding: 15px; font-size: ${imageDescFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${imageDescription}</p>
                </div>
                <div class="benefits-grid" style="width: 60%; display: grid; grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, auto); gap: 15px; overflow: visible;">
                    ${benefitsHtml}
                </div>
            </div>
        </div>
    `;
}

function renderIconGrid(content, template) {
    const title = content.title || 'Categories';
    const categories = content.categories || [];
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const titleFontSize = Math.max(24, Math.min(32, 32 * (40 / Math.max(40, titleLength))));
    
    let categoriesHtml = '';
    
    categories.slice(0, 8).forEach((category) => {
        const categoryName = category.name || '';
        const categoryDesc = category.description || '';
        
        // Calculate dynamic font sizes for category content
        const categoryNameLength = categoryName.length;
        const categoryDescLength = categoryDesc.length;
        
        const categoryNameFontSize = Math.max(12, Math.min(16, 16 * (20 / Math.max(20, categoryNameLength))));
        const categoryDescFontSize = Math.max(10, Math.min(12, 12 * (40 / Math.max(40, categoryDescLength))));
        
        categoriesHtml += `
            <div class="category-item" style="background-color: white; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: auto; min-height: 122px; display: flex; flex-direction: column; align-items: center;">
                <div class="category-icon" style="background-color: #8278F0; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px auto;">
                    <span style="font-size: 20px; color: white;">⭐</span>
                </div>
                <h3 style="color: ${template.colors.primary}; margin: 0 0 8px 0; font-size: ${categoryNameFontSize}px; line-height: 1.2; height: auto; word-wrap: break-word; white-space: normal; overflow: visible;">
                    ${categoryName}
                </h3>
                <p style="color: ${template.colors.text}; font-size: ${categoryDescFontSize}px; line-height: 1.3; margin: 0; flex-grow: 1; word-wrap: break-word; white-space: normal; overflow: visible;">
                    ${categoryDesc}
                </p>
            </div>
        `;
    });
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 25px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <div class="categories-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(2, auto); gap: 15px; max-height: none; overflow: visible;">
                ${categoriesHtml}
            </div>
        </div>
    `;
}

function renderSideBySideComparison(content, template) {
    const title = content.title || 'Challenge vs Solution';
    const leftTitle = content.leftTitle || 'The Challenge';
    const rightTitle = content.rightTitle || 'The Solution';
    const leftPoints = content.leftPoints || [];
    const rightPoints = content.rightPoints || [];
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const leftTitleLength = leftTitle.length;
    const rightTitleLength = rightTitle.length;
    
    const titleFontSize = Math.max(24, Math.min(32, 32 * (40 / Math.max(40, titleLength))));
    const leftTitleFontSize = Math.max(18, Math.min(22, 22 * (20 / Math.max(20, leftTitleLength))));
    const rightTitleFontSize = Math.max(18, Math.min(22, 22 * (20 / Math.max(20, rightTitleLength))));
    
    // Process points with responsive sizing
    let leftPointsHtml = '';
    leftPoints.slice(0, 3).forEach(point => {
        const pointLength = point.length;
        const pointFontSize = Math.max(12, Math.min(16, 16 * (80 / Math.max(80, pointLength))));
        
        leftPointsHtml += `<li style="color: ${template.colors.text}; margin-bottom: 10px; font-size: ${pointFontSize}px; line-height: 1.3; word-wrap: break-word; white-space: normal; overflow: visible;">${point}</li>`;
    });
    
    let rightPointsHtml = '';
    rightPoints.slice(0, 3).forEach(point => {
        const pointLength = point.length;
        const pointFontSize = Math.max(12, Math.min(16, 16 * (80 / Math.max(80, pointLength))));
        
        rightPointsHtml += `<li style="color: ${template.colors.text}; margin-bottom: 10px; font-size: ${pointFontSize}px; line-height: 1.3; word-wrap: break-word; white-space: normal; overflow: visible;">${point}</li>`;
    });
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 20px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <div class="comparison-container" style="display: flex; justify-content: space-between; width: 100%; gap: 20px; overflow: visible;">
                <div class="comparison-side" style="width: 48%; overflow: visible;">
                    <div class="image-placeholder" style="background-color: ${template.colors.secondary}; height: 150px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                        <p style="color: ${template.colors.background}; text-align: center;">Challenge image</p>
                    </div>
                    <h2 style="color: ${template.colors.primary}; margin-bottom: 10px; font-size: ${leftTitleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${leftTitle}</h2>
                    <ul style="padding-left: 20px; overflow: visible;">
                        ${leftPointsHtml}
                    </ul>
                </div>
                <div class="comparison-side" style="width: 48%; overflow: visible;">
                    <div class="image-placeholder" style="background-color: ${template.colors.accent}; height: 150px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                        <p style="color: ${template.colors.background}; text-align: center;">Solution image</p>
                    </div>
                    <h2 style="color: ${template.colors.primary}; margin-bottom: 10px; font-size: ${rightTitleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${rightTitle}</h2>
                    <ul style="padding-left: 20px; overflow: visible;">
                        ${rightPointsHtml}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function renderTimeline(content, template) {
    const title = content.title || 'Timeline';
    const events = content.events || [];
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const titleFontSize = Math.max(24, Math.min(32, 32 * (40 / Math.max(40, titleLength))));
    
    let eventsHtml = '';
    
    events.forEach((event, index) => {
        const year = event.year || '';
        const eventTitle = event.title || '';
        let description = event.description || '';
        
        // Calculate dynamic font sizes for event content
        const yearLength = year.length;
        const eventTitleLength = eventTitle.length;
        const descriptionLength = description.length;
        
        const yearFontSize = Math.max(14, Math.min(18, 18 * (8 / Math.max(8, yearLength))));
        const eventTitleFontSize = Math.max(14, Math.min(18, 18 * (30 / Math.max(30, eventTitleLength))));
        const descriptionFontSize = Math.max(12, Math.min(14, 14 * (100 / Math.max(100, descriptionLength))));
        
        // Add a period at the end of the description if it doesn't already end with one
        if (description && !description.endsWith('.')) {
            description += '.';
        }
        
        eventsHtml += `
            <div class="timeline-event" style="display: flex; margin-bottom: 10px; min-height: 60px; overflow: visible;">
                <div class="timeline-year" style="width: 80px; flex-shrink: 0; font-weight: bold; color: ${template.colors.secondary}; font-size: ${yearFontSize}px; text-align: right; padding-right: 15px; word-wrap: break-word; white-space: normal; overflow: visible;">
                    ${year}
                </div>
                <div class="timeline-connector" style="width: 30px; position: relative; flex-shrink: 0;">
                    <div style="position: absolute; top: 10px; bottom: ${index === events.length - 1 ? '10px' : '0'}; left: 50%; width: 2px; background-color: ${template.colors.secondary};"></div>
                    <div style="position: absolute; top: 6px; left: calc(50% - 6px); width: 12px; height: 12px; border-radius: 50%; background-color: ${template.colors.accent};"></div>
                </div>
                <div class="timeline-content" style="flex: 1; padding-left: 10px; overflow: visible;">
                    <h3 style="margin: 0 0 3px 0; color: ${template.colors.primary}; font-size: ${eventTitleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${eventTitle}</h3>
                    <p style="margin: 0; color: ${template.colors.text}; font-size: ${descriptionFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${description}</p>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 20px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <div class="timeline-container" style="padding-left: 2px; padding-right: 20px; overflow: visible;">
                ${eventsHtml}
            </div>
        </div>
    `;
}

function renderConclusion(content, template) {
    const title = content.title || 'Key Takeaways';
    const summary = content.summary || 'Summary of main points';
    const nextSteps = content.nextSteps || [];
    
    // Calculate dynamic font sizes
    const titleLength = title.length;
    const summaryLength = summary.length;
    
    const titleFontSize = Math.max(24, Math.min(36, 36 * (40 / Math.max(40, titleLength))));
    const summaryFontSize = Math.max(16, Math.min(22, 22 * (150 / Math.max(150, summaryLength))));
    
    let nextStepsHtml = '';
    nextSteps.forEach(step => {
        const stepLength = step.length;
        const stepFontSize = Math.max(16, Math.min(20, 20 * (50 / Math.max(50, stepLength))));
        
        nextStepsHtml += `<li style="color: ${template.colors.text}; margin-bottom: 15px; font-size: ${stepFontSize}px; line-height: 1.3; word-wrap: break-word; white-space: normal; overflow: visible;">${step}</li>`;
    });
    
    return `
        <div class="preview-slide" style="background-color: ${template.colors.background}; padding: 30px; min-height: 400px; height: auto; overflow: visible;">
            <h1 style="color: ${template.colors.primary}; margin-bottom: 15px; font-size: ${titleFontSize}px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">${title}</h1>
            <p style="color: ${template.colors.secondary}; margin-bottom: 20px; font-size: ${summaryFontSize}px; line-height: 1.4; word-wrap: break-word; white-space: normal; overflow: visible;">${summary}</p>
            ${nextSteps.length > 0 ? `
                <h3 style="color: ${template.colors.primary}; margin-top: 30px; font-size: 24px; line-height: 1.2; word-wrap: break-word; white-space: normal; overflow: visible;">Next Steps</h3>
                <ul style="color: ${template.colors.text}; padding-left: 40px; margin-top: 10px; overflow: visible;">
                    ${nextStepsHtml}
                </ul>
            ` : ''}
        </div>
    `;
}

// end 


function createBenefitsGridForm(content) {
    const title = content.title || '';
    const imageDescription = content.imageDescription || '';
    const benefits = content.benefits || [{}, {}, {}, {}];
    
    let benefitsFields = '';
    for (let i = 0; i < 4; i++) {
        const benefit = benefits[i] || {};
        benefitsFields += `
            <div class="benefit-item">
                <h5>Benefit ${i+1}</h5>
                ${createFormField('Benefit Title', `benefit-${i}-title`, benefit.title || '')}
                ${createTextAreaField('Benefit Description', `benefit-${i}-description`, benefit.description || '')}
            </div>
        `;
    }
    
    return `
        <h3>Edit Benefits Grid</h3>
        ${createFormField('Title', 'title', title)}
        ${createFormField('Image Description', 'imageDescription', imageDescription)}
        <h4>Benefits</h4>
        ${benefitsFields}
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
        <button id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
    `;
}
function createConclusionForm(content) {
    const title = content.title || '';
    const summary = content.summary || '';
    const nextSteps = content.nextSteps || ['', '', ''];
    
    let nextStepsFields = '';
    for (let i = 0; i < 3; i++) {
        nextStepsFields += `
            <div class="form-group">
                <label for="next-step-${i}">Next Step ${i+1}:</label>
                <input type="text" id="next-step-${i}" name="next-step-${i}" value="${escapeHTML(nextSteps[i] || '')}" class="form-control">
            </div>
        `;
    }
    
    return `
        <h3>Edit Conclusion</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-group">
            <label for="summary">Summary:</label>
            <textarea id="summary" name="summary" rows="3" class="form-control">${escapeHTML(summary)}</textarea>
        </div>
        <h4>Next Steps</h4>
        ${nextStepsFields}
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function collectFormData(layout) {
    const formData = {};
    
    switch(layout) {
        case 'titleAndBullets':
            formData.title = document.getElementById('title').value;
            formData.bullets = [];
            for (let i = 0; i < 5; i++) {
                const bulletElement = document.getElementById(`bullet-${i}`);
                if (bulletElement && bulletElement.value.trim()) {
                    formData.bullets.push(bulletElement.value);
                }
            }
            break;
            
        case 'quote':
            formData.quote = document.getElementById('quote').value;
            formData.author = document.getElementById('author').value;
            break;
            
        case 'imageAndParagraph':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.paragraph = document.getElementById('paragraph').value;
            break;
            
        case 'twoColumn':
            formData.title = document.getElementById('title').value;
            formData.column1Title = document.getElementById('column1Title').value;
            formData.column1Content = document.getElementById('column1Content').value;
            formData.column2Title = document.getElementById('column2Title').value;
            formData.column2Content = document.getElementById('column2Content').value;
            break;
            
        case 'titleOnly':
            formData.title = document.getElementById('title').value;
            formData.subtitle = document.getElementById('subtitle').value;
            break;
            
        // New form data collectors
        case 'imageWithFeatures':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.features = [];
            for (let i = 0; i < 4; i++) {
                const titleElement = document.getElementById(`feature-${i}-title`);
                const descriptionElement = document.getElementById(`feature-${i}-description`);
                if (titleElement && descriptionElement && (titleElement.value.trim() || descriptionElement.value.trim())) {
                    formData.features.push({
                        title: titleElement.value,
                        description: descriptionElement.value
                    });
                }
            }
            break;
            
        case 'numberedFeatures':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.features = [];
            for (let i = 0; i < 4; i++) {
                const titleElement = document.getElementById(`feature-${i}-title`);
                const descriptionElement = document.getElementById(`feature-${i}-description`);
                if (titleElement && descriptionElement && (titleElement.value.trim() || descriptionElement.value.trim())) {
                    formData.features.push({
                        number: i + 1,
                        title: titleElement.value,
                        description: descriptionElement.value
                    });
                }
            }
            break;
            
        case 'pricingTable':
            formData.title = document.getElementById('title').value;
            formData.priceAmount = document.getElementById('priceAmount').value;
            formData.percentage = document.getElementById('percentage').value;
            formData.priceDescription = document.getElementById('priceDescription').value;
            formData.percentageDescription = document.getElementById('percentageDescription').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            break;
            
        case 'benefitsGrid':
            formData.title = document.getElementById('title').value;
            formData.imageDescription = document.getElementById('imageDescription').value;
            formData.benefits = [];
            for (let i = 0; i < 4; i++) {
                const titleElement = document.getElementById(`benefit-${i}-title`);
                const descriptionElement = document.getElementById(`benefit-${i}-description`);
                if (titleElement && descriptionElement && (titleElement.value.trim() || descriptionElement.value.trim())) {
                    formData.benefits.push({
                        title: titleElement.value,
                        description: descriptionElement.value
                    });
                }
            }
            break;
            
        case 'iconGrid':
            formData.title = document.getElementById('title').value;
            formData.categories = [];
            for (let i = 0; i < 8; i++) {
                const nameElement = document.getElementById(`category-${i}-name`);
                const descriptionElement = document.getElementById(`category-${i}-description`);
                if (nameElement && descriptionElement && (nameElement.value.trim() || descriptionElement.value.trim())) {
                    formData.categories.push({
                        name: nameElement.value,
                        description: descriptionElement.value
                    });
                }
            }
            break;
            
        case 'sideBySideComparison':
            formData.title = document.getElementById('title').value;
            formData.leftTitle = document.getElementById('leftTitle').value;
            formData.rightTitle = document.getElementById('rightTitle').value;
            
            formData.leftPoints = [];
            for (let i = 0; i < 3; i++) {
                const pointElement = document.getElementById(`left-point-${i}`);
                if (pointElement && pointElement.value.trim()) {
                    formData.leftPoints.push(pointElement.value);
                }
            }
            
            formData.rightPoints = [];
            for (let i = 0; i < 3; i++) {
                const pointElement = document.getElementById(`right-point-${i}`);
                if (pointElement && pointElement.value.trim()) {
                    formData.rightPoints.push(pointElement.value);
                }
            }
            break;
            
        case 'timeline':
            formData.title = document.getElementById('title').value;
            formData.events = [];
            
            // Find all event forms and collect data
            const eventForms = document.querySelectorAll('.timeline-event-form');
            eventForms.forEach((form, index) => {
                const yearElement = document.getElementById(`event-${index}-year`);
                const titleElement = document.getElementById(`event-${index}-title`);
                const descriptionElement = document.getElementById(`event-${index}-description`);
                
                if (yearElement && titleElement && descriptionElement && 
                    (yearElement.value.trim() || titleElement.value.trim() || descriptionElement.value.trim())) {
                    formData.events.push({
                        year: yearElement.value,
                        title: titleElement.value,
                        description: descriptionElement.value
                    });
                }
            });
            break;
        case 'conclusion':
            formData.title = document.getElementById('title').value;
            formData.summary = document.getElementById('summary').value;
            formData.nextSteps = [];
            for (let i = 0; i < 3; i++) {
                const step = document.getElementById(`next-step-${i}`).value;
                if (step.trim()) {
                    formData.nextSteps.push(step);
                }
            }
            break;
    }
    
    return formData;
}
function createImageAndParagraphForm(content) {
    const title = content.title || '';
    const paragraph = content.paragraph || '';
    const imageDescription = content.imageDescription || '';
    
    return `
        <h3>Edit Image and Paragraph</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-group">
            <label for="imageDescription">Image Description:</label>
            <input type="text" id="imageDescription" name="imageDescription" value="${escapeHTML(imageDescription)}" class="form-control">
        </div>
        <div class="form-group">
            <label for="paragraph">Paragraph:</label>
            <textarea id="paragraph" name="paragraph" rows="5" class="form-control">${escapeHTML(paragraph)}</textarea>
        </div>
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function createPricingTableForm(content) {
    const title = content.title || '';
    const priceAmount = content.priceAmount || '';
    const percentage = content.percentage || '';
    const priceDescription = content.priceDescription || '';
    const percentageDescription = content.percentageDescription || '';
    const imageDescription = content.imageDescription || '';
    
    return `
        <h3>Edit Pricing Table</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-row">
            <div class="col">
                <h4>Price Amount</h4>
                <div class="form-group">
                    <label for="priceAmount">Amount:</label>
                    <input type="text" id="priceAmount" name="priceAmount" value="${escapeHTML(priceAmount)}" class="form-control">
                </div>
                <div class="form-group">
                    <label for="priceDescription">Description:</label>
                    <input type="text" id="priceDescription" name="priceDescription" value="${escapeHTML(priceDescription)}" class="form-control">
                </div>
            </div>
            <div class="col">
                <h4>Percentage</h4>
                <div class="form-group">
                    <label for="percentage">Percentage:</label>
                    <input type="text" id="percentage" name="percentage" value="${escapeHTML(percentage)}" class="form-control">
                </div>
                <div class="form-group">
                    <label for="percentageDescription">Description:</label>
                    <input type="text" id="percentageDescription" name="percentageDescription" value="${escapeHTML(percentageDescription)}" class="form-control">
                </div>
            </div>
        </div>
        <div class="form-group">
            <label for="imageDescription">Image Description:</label>
            <input type="text" id="imageDescription" name="imageDescription" value="${escapeHTML(imageDescription)}" class="form-control">
        </div>
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}

function createTitleAndBulletsForm(content) {
    const title = content.title || '';
    const bullets = content.bullets || ['', '', '', '', ''];
    
    let bulletFields = '';
    for (let i = 0; i < 5; i++) {
        const bullet = bullets[i] || '';
        bulletFields += `
            <div class="form-group">
                <label for="bullet-${i}">Bullet ${i+1}:</label>
                <input type="text" id="bullet-${i}" name="bullet-${i}" value="${escapeHTML(bullet)}" class="form-control">
            </div>
        `;
    }
    
    return `
        <h3>Edit Title and Bullets</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <h4>Bullet Points</h4>
        ${bulletFields}
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function createNumberedFeaturesForm(content) {
    const title = content.title || '';
    const imageDescription = content.imageDescription || '';
    const features = content.features || [{}, {}, {}, {}];
    
    let featuresFields = '';
    for (let i = 0; i < 4; i++) {
        const feature = features[i] || {};
        featuresFields += `
            <div class="feature-item">
                <h5>Feature ${i+1}</h5>
                <div class="form-group">
                    <label for="feature-${i}-title">Feature Title:</label>
                    <input type="text" id="feature-${i}-title" name="feature-${i}-title" value="${escapeHTML(feature.title || '')}" class="form-control">
                </div>
                <div class="form-group">
                    <label for="feature-${i}-description">Description:</label>
                    <textarea id="feature-${i}-description" name="feature-${i}-description" class="form-control">${escapeHTML(feature.description || '')}</textarea>
                </div>
            </div>
        `;
    }
    
    return `
        <h3>Edit Numbered Features</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-group">
            <label for="imageDescription">Image Description:</label>
            <input type="text" id="imageDescription" name="imageDescription" value="${escapeHTML(imageDescription)}" class="form-control">
        </div>
        <h4>Features</h4>
        ${featuresFields}
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function createQuoteForm(content) {
    const quote = content.quote || '';
    const author = content.author || '';
    
    return `
        <h3>Edit Quote</h3>
        <div class="form-group">
            <label for="quote">Quote:</label>
            <textarea id="quote" name="quote" rows="4" class="form-control">${escapeHTML(quote)}</textarea>
        </div>
        <div class="form-group">
            <label for="author">Author:</label>
            <input type="text" id="author" name="author" value="${escapeHTML(author)}" class="form-control">
        </div>
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function createTwoColumnForm(content) {
    const title = content.title || '';
    const column1Title = content.column1Title || '';
    const column1Content = content.column1Content || '';
    const column2Title = content.column2Title || '';
    const column2Content = content.column2Content || '';
    
    return `
        <h3>Edit Two Column Layout</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-row">
            <div class="col">
                <h4>Left Column</h4>
                <div class="form-group">
                    <label for="column1Title">Column 1 Title:</label>
                    <input type="text" id="column1Title" name="column1Title" value="${escapeHTML(column1Title)}" class="form-control">
                </div>
                <div class="form-group">
                    <label for="column1Content">Column 1 Content:</label>
                    <textarea id="column1Content" name="column1Content" rows="5" class="form-control">${escapeHTML(typeof column1Content === 'string' ? column1Content : '')}</textarea>
                </div>
            </div>
            <div class="col">
                <h4>Right Column</h4>
                <div class="form-group">
                    <label for="column2Title">Column 2 Title:</label>
                    <input type="text" id="column2Title" name="column2Title" value="${escapeHTML(column2Title)}" class="form-control">
                </div>
                <div class="form-group">
                    <label for="column2Content">Column 2 Content:</label>
                    <textarea id="column2Content" name="column2Content" rows="5" class="form-control">${escapeHTML(typeof column2Content === 'string' ? column2Content : '')}</textarea>
                </div>
            </div>
        </div>
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function createSideBySideComparisonForm(content) {
    const title = content.title || '';
    const leftTitle = content.leftTitle || '';
    const rightTitle = content.rightTitle || '';
    const leftPoints = content.leftPoints || ['', '', ''];
    const rightPoints = content.rightPoints || ['', '', ''];
    
    let leftPointsFields = '';
    for (let i = 0; i < 3; i++) {
        leftPointsFields += `
            <div class="form-group">
                <label for="left-point-${i}">Point ${i+1}:</label>
                <input type="text" id="left-point-${i}" name="left-point-${i}" value="${escapeHTML(leftPoints[i] || '')}" class="form-control">
            </div>
        `;
    }
    
    let rightPointsFields = '';
    for (let i = 0; i < 3; i++) {
        rightPointsFields += `
            <div class="form-group">
                <label for="right-point-${i}">Point ${i+1}:</label>
                <input type="text" id="right-point-${i}" name="right-point-${i}" value="${escapeHTML(rightPoints[i] || '')}" class="form-control">
            </div>
        `;
    }
    
    return `
        <h3>Edit Side by Side Comparison</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-row">
            <div class="col">
                <h4>Left Side</h4>
                <div class="form-group">
                    <label for="leftTitle">Left Title:</label>
                    <input type="text" id="leftTitle" name="leftTitle" value="${escapeHTML(leftTitle)}" class="form-control">
                </div>
                <h5>Left Points</h5>
                ${leftPointsFields}
            </div>
            <div class="col">
                <h4>Right Side</h4>
                <div class="form-group">
                    <label for="rightTitle">Right Title:</label>
                    <input type="text" id="rightTitle" name="rightTitle" value="${escapeHTML(rightTitle)}" class="form-control">
                </div>
                <h5>Right Points</h5>
                ${rightPointsFields}
            </div>
        </div>
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
function createImageWithFeaturesForm(content) {
    const title = content.title || '';
    const imageDescription = content.imageDescription || '';
    const features = content.features || [{}, {}, {}, {}];
    
    let featuresFields = '';
    for (let i = 0; i < 4; i++) {
        const feature = features[i] || {};
        featuresFields += `
            <div class="feature-item">
                <h5>Feature ${i+1}</h5>
                <div class="form-group">
                    <label for="feature-${i}-title">Feature Title:</label>
                    <input type="text" id="feature-${i}-title" name="feature-${i}-title" value="${escapeHTML(feature.title || '')}" class="form-control">
                </div>
                <div class="form-group">
                    <label for="feature-${i}-description">Description:</label>
                    <textarea id="feature-${i}-description" name="feature-${i}-description" class="form-control">${escapeHTML(feature.description || '')}</textarea>
                </div>
            </div>
        `;
    }
    
    return `
        <h3>Edit Image with Features</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-group">
            <label for="imageDescription">Image Description:</label>
            <input type="text" id="imageDescription" name="imageDescription" value="${escapeHTML(imageDescription)}" class="form-control">
        </div>
        <h4>Features</h4>
        ${featuresFields}
        <div class="edit-actions">
            <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
            <button type="button" id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
        </div>
    `;
}
// Function to create edit form based on layout type
function createEditForm(layout, content) {
    switch(layout) {
        case 'titleAndBullets':
            return createTitleAndBulletsForm(content);
        case 'quote':
            return createQuoteForm(content);
        case 'imageAndParagraph':
            return createImageAndParagraphForm(content);
        case 'twoColumn':
            return createTwoColumnForm(content);
        case 'titleOnly':
            return createTitleOnlyForm(content);
        // New layout forms
        case 'imageWithFeatures':
            return createImageWithFeaturesForm(content);
        case 'numberedFeatures':
            return createNumberedFeaturesForm(content);
        case 'pricingTable':
            return createPricingTableForm(content);
        case 'benefitsGrid':
            return createBenefitsGridForm(content);
        case 'iconGrid':
            return createIconGridForm(content);
        case 'sideBySideComparison':
            return createSideBySideComparisonForm(content);
        case 'timeline':
            return createTimelineForm(content);
        case 'conclusion':
            return createConclusionForm(content);
        default:
            return `<div class="form-error">Unknown layout type: ${layout}</div>`;
    }
}

// Add to layouts.js
function createTitleOnlyForm(content) {
    const title = content.title || '';
    const subtitle = content.subtitle || '';
    
    return `
        <h3>Edit Title Slide</h3>
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control">
        </div>
        <div class="form-group">
            <label for="subtitle">Subtitle:</label>
            <input type="text" id="subtitle" name="subtitle" value="${escapeHTML(subtitle)}" class="form-control">
        </div>
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
        <button id="cancel-edit-btn" class="btn btn-secondary">Cancel</button>
    `;
}

function createIconGridForm(content) {
    const title = content.title || '';
    // FIXED: Changed from 5 to 8 categories
    const categories = content.categories || [{}, {}, {}, {}, {}, {}, {}, {}];
    
    let categoriesFields = '';
    // FIXED: Changed from 5 to 8 categories
    for (let i = 0; i < 8; i++) {
        const category = categories[i] || {};
        categoriesFields += `
            <div class="category-item" style="margin-bottom: 30px; padding-bottom: 15px; border-bottom: 1px solid #eee; width: 100%;">
                <h3 style="text-align: left !important; margin-bottom: 15px; display: block; width: 100%; margin-left: 0; padding-left: 0;">Category ${i+1}</h3>
                <div class="form-group" style="margin-bottom: 15px; width: 100%; text-align: left !important;">
                    <label for="category-${i}-name" style="text-align: left !important; display: block;">Category Name:</label>
                    <input type="text" id="category-${i}-name" name="category-${i}-name" value="${escapeHTML(category.name || '')}" class="form-control" style="width: 100%;">
                </div>
                <div class="form-group" style="width: 100%; text-align: left !important;">
                    <label for="category-${i}-description" style="text-align: left !important; display: block;">Category Description:</label>
                    <textarea id="category-${i}-description" name="category-${i}-description" class="form-control" style="width: 100%; min-height: 100px; resize: vertical;">${escapeHTML(category.description || '')}</textarea>
                </div>
            </div>
        `;
    }
    
    return `
        <div style="width: 100%; padding: 0; margin: 0; text-align: left !important;">
            <h3 style="text-align: left !important; margin-top: 0; margin-bottom: 20px; display: block; width: 100%;">Edit Icon Grid</h3>
            <div class="form-group" style="margin-bottom: 20px; width: 100%; text-align: left !important;">
                <label for="title" style="text-align: left !important; display: block;">Title:</label>
                <input type="text" id="title" name="title" value="${escapeHTML(title)}" class="form-control" style="width: 100%;">
            </div>
            <h4 style="text-align: left !important; margin-bottom: 20px; display: block; width: 100%;">Categories (8 required)</h4>
            <div class="categories-container" style="padding: 0; margin: 0; width: 100%; text-align: left !important;">
                ${categoriesFields}
            </div>
            <div class="edit-actions" style="margin-top: 20px; text-align: right;">
                <button type="button" id="save-edit-btn" class="btn btn-primary">Save Changes</button>
                <button type="button" id="cancel-edit-btn" class="btn btn-secondary" style="margin-left: 10px;">Cancel</button>
            </div>
        </div>
    `;
}

function createFormField(label, id, value) {
    return `
        <div class="form-group">
            <label for="${id}">${label}</label>
            <input type="text" id="${id}" name="${id}" value="${escapeHTML(value || '')}" class="form-control">
        </div>
    `;
}

// Helper function to escape HTML in content
function escapeHTML(str) {
    if (!str || typeof str !== 'string') return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
// Helper function to create a text area field
function createTextAreaField(label, id, value) {
    return `
        <div class="form-group">
            <label for="${id}">${label}</label>
            <textarea id="${id}" class="form-control">${value || ''}</textarea>
        </div>
    `;
}

function getLayoutById(layoutId) {
    return layouts.find(layout => layout.id === layoutId) || null;
}

// function showLayoutSelector() {
//     const currentSlide = appState.slides[appState.currentSlideIndex];
//     if (!currentSlide) return;
    
//     const editForm = document.getElementById('edit-form');
//     const slidePreview = document.getElementById('slide-preview');
    
//     // Create the layout selector
//     const layouts = window.ppgLayouts.layouts;
    
//     let layoutOptionsHtml = '<div class="layout-options">';
//     layouts.forEach(layout => {
//         layoutOptionsHtml += `
//             <div class="layout-option ${layout.id === currentSlide.layout ? 'selected' : ''}" 
//                  data-layout="${layout.id}">
//                 <div class="layout-icon"><i class="fas ${layout.icon}"></i></div>
//                 <div class="layout-info">
//                     <h4>${layout.name}</h4>
//                     <p>${layout.description}</p>
//                 </div>
//             </div>
//         `;
//     });
//     layoutOptionsHtml += '</div>';
    
//     // Create the full selector form
//     const formHtml = `
//         <div class="layout-selector">
//             <h2>Change Slide Layout</h2>
//             <p class="warning">Changing layout will reset the slide content. Save any important content first.</p>
            
//             ${layoutOptionsHtml}
            
//             <div class="layout-selector-actions">
//                 <button id="change-layout-btn" class="btn btn-primary">Change Layout</button>
//                 <button id="cancel-layout-btn" class="btn btn-secondary">Cancel</button>
//             </div>
//         </div>
//     `;
    
//     // Set the form content
//     editForm.innerHTML = formHtml;
    
//     // Show the form and hide the preview
//     editForm.classList.remove('hidden');
//     slidePreview.classList.add('hidden');
    
//     // Mark that we're in layout selection mode
//     appState.editMode = 'layout';
    
//     // Add event listeners
//     document.getElementById('change-layout-btn').addEventListener('click', changeLayout);
//     document.getElementById('cancel-layout-btn').addEventListener('click', cancelEdit);
    
//     // Add click events to layout options
//     const layoutOptions = document.querySelectorAll('.layout-option');
//     layoutOptions.forEach(option => {
//         option.addEventListener('click', () => {
//             // Deselect all options
//             layoutOptions.forEach(opt => opt.classList.remove('selected'));
//             // Select the clicked option
//             option.classList.add('selected');
//         });
//     });
// }

// Change the current slide's layout
function changeLayout() {
    const selectedLayout = document.querySelector('.layout-option.selected');
    if (!selectedLayout) {
        alert('Please select a layout');
        return;
    }
    
    const newLayout = selectedLayout.dataset.layout;
    const currentSlide = appState.slides[appState.currentSlideIndex];
    
    // Only proceed if the layout is actually changing
    if (newLayout === currentSlide.layout) {
        cancelEdit();
        return;
    }
    
    // Confirm the change
    const confirmChange = confirm('Changing layout will reset slide content. Are you sure?');
    if (!confirmChange) {
        return;
    }
    
    // Preserve title if possible
    const oldTitle = currentSlide.content.title || '';
    
    // Reset content with new layout defaults
    currentSlide.layout = newLayout;
    currentSlide.content = generateDefaultContent(newLayout);
    
    // Try to preserve the title
    if (oldTitle && currentSlide.content.title !== undefined) {
        currentSlide.content.title = oldTitle;
    }
    
    // Mark as modified
    appState.isModified = true;
    
    // Return to preview mode and render the updated slide
    cancelEdit();
    renderCurrentSlide();
    renderSlidesList();
    
    showNotification('Slide layout changed successfully!', 'success');
}

// Generate default content for a new layout
function generateDefaultContent(layout) {
    const topic = appState.topic || 'Presentation';
    
    switch(layout) {
        case 'titleOnly':
            return {
                title: topic,
                subtitle: 'Presentation Overview'
            };
        case 'titleAndBullets':
            return {
                title: `Key Points about ${topic}`,
                bullets: [
                    'Point 1',
                    'Point 2',
                    'Point 3'
                ]
            };
        case 'quote':
            return {
                quote: 'Insert your quote here',
                author: 'Author Name'
            };
        case 'imageAndParagraph':
            return {
                title: topic,
                imageDescription: 'Image',
                paragraph: 'Enter your paragraph text here.'
            };
        case 'twoColumn':
            return {
                title: topic,
                column1Title: 'Column 1',
                column1Content: 'Content for first column',
                column2Title: 'Column 2',
                column2Content: 'Content for second column'
            };
        case 'pricingTable':
            return {
                title: `Pricing Model: ${topic}`,
                priceAmount: '₹30,000',
                percentage: '30%',
                priceDescription: 'Base cost per unit',
                percentageDescription: 'Profit margin'
            };
        case 'imageWithFeatures':
            return {
                title: `Features of ${topic}`,
                imageDescription: 'Image',
                features: [
                    {title: 'Feature 1', description: 'Description of feature 1'},
                    {title: 'Feature 2', description: 'Description of feature 2'},
                    {title: 'Feature 3', description: 'Description of feature 3'},
                    {title: 'Feature 4', description: 'Description of feature 4'}
                ]
            };
        case 'benefitsGrid':
            return {
                title: `Benefits of ${topic}`,
                imageDescription: 'Image',
                benefits: [
                    {title: 'Benefit 1', description: 'Description of benefit 1'},
                    {title: 'Benefit 2', description: 'Description of benefit 2'},
                    {title: 'Benefit 3', description: 'Description of benefit 3'},
                    {title: 'Benefit 4', description: 'Description of benefit 4'}
                ]
            };
        case 'numberedFeatures':
            return {
                title: `Key Steps for ${topic}`,
                imageDescription: 'Image',
                features: [
                    {number: 1, title: 'Step 1', description: 'Description of step 1'},
                    {number: 2, title: 'Step 2', description: 'Description of step 2'},
                    {number: 3, title: 'Step 3', description: 'Description of step 3'},
                    {number: 4, title: 'Step 4', description: 'Description of step 4'}
                ]
            };
        case 'timeline':
            return {
                title: `Evolution of ${topic}`,
                events: [
                    {year: '2000', title: 'First milestone', description: 'Description of first milestone'},
                    {year: '2010', title: 'Second milestone', description: 'Description of second milestone'},
                    {year: '2020', title: 'Third milestone', description: 'Description of third milestone'},
                    {year: 'Present', title: 'Current state', description: 'Description of current state'}
                ]
            };
        default:
            return {};
    }
}
