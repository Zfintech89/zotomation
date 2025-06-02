// templates.js - Defines the available slide templates

const templates = [
    {
        id: 'corporate',
        name: 'Corporate',
        description: 'Professional blue theme for business presentations',
        previewClass: 'corporate-preview',
        colors: {
            primary: '#0f4c81',
            secondary: '#6e9cc4',
            accent: '#f2b138',
            background: '#ffffff',
            text: '#333333'
        }
    },
    {
    "id": "creative-updated",
    "name": "Creative Updated",
    "description": "Modern, vibrant palette with clean typography for expressive presentations",
    "previewClass": "creative-updated-preview",
    "colors": {
        "primary": "#3A86FF",
        "secondary": "#8338EC",
        "accent": "#00CFC1",
        "background": "#FDFDFD",
        "text": "#1D1D1D"
    },
    "font": "Inter"
},
// {
//     "id": "gamma-updated",
//     "name": "gamma Updated",
//     "description": "Modern, vibrant palette with clean typography for expressive presentations",
//     "previewClass": "creative-updated-preview",
//     "colors": {
//         "primary": "#c91313",
//         "secondary": "#999999",
//         "accent": "#740b0b",
//         "background": "#0a0a0a",
//         "text": "#ffffff"
//     },
//     "font": "Inter"
// },
    {
        id: 'creative',
        name: 'Creative',
        description: 'Colorful theme for creative presentations',
        previewClass: 'creative-preview',
        colors: {
            primary: '#ff6b6b',
            secondary: '#4ecdc4',
            accent: '#ffd166',
            background: '#f9f1e6',
            text: '#5a3921'
        }
    },
    {
        id: 'minimal',
        name: 'Minimal',
        description: 'Clean, minimalist theme with subtle colors',
        previewClass: 'minimal-preview',
        colors: {
            primary: '#2c3e50',
            secondary: '#95a5a6',
            accent: '#e74c3c',
            background: '#f8f8f8',
            text: '#222222'
        }
    },
    {
        id: 'nature',
        name: 'Nature',
        description: 'Organic green theme inspired by natural landscapes',
        previewClass: 'nature-preview',
        colors: {
            primary: '#2d6a4f',
            secondary: '#74c69d',
            accent: '#ffb703',
            background: '#f1faee',
            text: '#1b4332'
        }
    },
    {
        id: 'tech',
        name: 'Technology',
        description: 'Modern theme with sleek colors for tech presentations',
        previewClass: 'tech-preview',
        colors: {
            primary: '#3a0ca3',
            secondary: '#4361ee',
            accent: '#7209b7',
            background: '#f8f9fa',
            text: '#212529'
        }
    },
    {
        id: 'gradient',
        name: 'Gradient',
        description: 'Smooth gradient backgrounds with complementary colors',
        previewClass: 'gradient-preview',
        colors: {
            primary: '#8338ec',
            secondary: '#3a86ff',
            accent: '#ff006e',
            background: '#ffffff',
            text: '#2b2d42'
        }
    },
    {
        id: 'pastel',
        name: 'Pastel',
        description: 'Soft pastel colors for a gentle, approachable feel',
        previewClass: 'pastel-preview',
        colors: {
            primary: '#9d8189',
            secondary: '#d8e2dc',
            accent: '#ffcad4',
            background: '#f7ede2',
            text: '#6d6875'
        }
    },
    {
        id: 'energetic',
        name: 'Energetic',
        description: 'Vibrant colors for impactful, dynamic presentations',
        previewClass: 'energetic-preview',
        colors: {
            primary: '#f72585',
            secondary: '#7209b7',
            accent: '#4cc9f0',
            background: '#ffffff',
            text: '#2b2d42'
        }
    },
    {
        id: 'earthy',
        name: 'Earthy',
        description: 'Warm, natural tones inspired by earth elements',
        previewClass: 'earthy-preview',
        colors: {
            primary: '#996633',
            secondary: '#dda15e',
            accent: '#bc6c25',
            background: '#fefae0',
            text: '#283618'
        }
    },
    {
        id: 'ocean',
        name: 'Ocean',
        description: 'Calming blue tones inspired by the sea',
        previewClass: 'ocean-preview',
        colors: {
            primary: '#003566',
            secondary: '#468faf',
            accent: '#00b4d8',
            background: '#f0f7f9',
            text: '#001845'
        }
    },
    {
        id: 'monochrome',
        name: 'Monochrome',
        description: 'Elegant grayscale design with a single accent color',
        previewClass: 'monochrome-preview',
        colors: {
            primary: '#2b2d42',
            secondary: '#8d99ae',
            accent: '#ef233c',
            background: '#edf2f4',
            text: '#1a1a1a'
        }
    },
    {
        id: 'sunset',
        name: 'Sunset',
        description: 'Warm gradient of sunset colors for a striking presentation',
        previewClass: 'sunset-preview',
        colors: {
            primary: '#ff9e00',
            secondary: '#ff4d00',
            accent: '#7678ed',
            background: '#fff1e6',
            text: '#3d405b'
        }
    },
    {
        id: 'botanical',
        name: 'Botanical',
        description: 'Fresh theme inspired by plants and botanical illustrations',
        previewClass: 'botanical-preview',
        colors: {
            primary: '#386641',
            secondary: '#a7c957',
            accent: '#fb8500',
            background: '#f8f9fa',
            text: '#283618'
        }
    }
];



function initializeTemplateSelector() {
    console.log('[templates.js] initializeTemplateSelector called');
    const templatesContainer = document.getElementById('templates-container');
    
    if (!templatesContainer) {
        console.error('[templates.js] Templates container not found');
        return;
    }
    
    // Check if templates are already initialized
    if (templatesContainer.querySelector('.template-selection-wrapper')) {
        console.log('[templates.js] Templates already initialized, skipping');
        return;
    }
    
    console.log('[templates.js] templatesContainer found:', !!templatesContainer);
    
    // Create the templates wrapper and toggle button
    const wrapperHtml = `
        <div class="template-selection-wrapper">
            <div class="template-toggle-button" id="template-toggle-button">
                <span id="selected-template-name">Select Template: Creative</span>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="templates-panel" id="templates-panel">
                <div class="templates-grid" id="templates-grid"></div>
            </div>
        </div>
    `;
    
    // Replace the container content
    templatesContainer.innerHTML = wrapperHtml;
    
    // Get the grid container
    const templatesGrid = document.getElementById('templates-grid');
    
    // Add template options to the grid
    templates.forEach((template, index) => {
        console.log(`[templates.js] Adding template ${index + 1}/${templates.length}: ${template.id}`);
        const templateElement = document.createElement('div');
        templateElement.className = 'template-option';
        templateElement.dataset.templateId = template.id;
        
        templateElement.innerHTML = `
            <div class="template-preview" style="background-color: ${template.colors.background}; color: ${template.colors.text}">
                <div style="height: 8px; background-color: ${template.colors.primary}"></div>
                <div style="text-align: center; margin-top: 15px; font-size: 12px;">
                    <span style="color: ${template.colors.primary}">${template.name}</span>
                </div>
            </div>
            <p>${template.name}</p>
        `;
        
        templateElement.addEventListener('click', () => {
            console.log(`[templates.js] Template selected: ${template.id}`);
            // Remove selected class from all templates
            document.querySelectorAll('.template-option').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Add selected class to this template
            templateElement.classList.add('selected');
            
            // Store the selected template
            window.selectedTemplateId = template.id;
            console.log(`[templates.js] Set window.selectedTemplateId to: ${template.id}`);
            
            // Update the toggle button text
            const selectedName = document.getElementById('selected-template-name');
            if (selectedName) {
                selectedName.textContent = `Select Template: ${template.name}`;
            }
            
            // Close the grid after selection
            const templatesPanel = document.getElementById('templates-panel');
            if (templatesPanel) {
                templatesPanel.style.display = 'none';
            }
            
            // Update toggle icon
            const toggleIcon = document.querySelector('.toggle-icon');
            if (toggleIcon) {
                toggleIcon.textContent = '▼';
            }
        });
        
        templatesGrid.appendChild(templateElement);
    });
    
    // Set up toggle functionality
    const toggleButton = document.getElementById('template-toggle-button');
    const templatesPanel = document.getElementById('templates-panel');
    
    // Hide grid initially
    templatesPanel.style.display = 'none';
    
    // Toggle function
    function toggleTemplatesGrid() {
        const isVisible = templatesPanel.style.display !== 'none';
        templatesPanel.style.display = isVisible ? 'none' : 'block';
        
        // Update toggle icon
        const toggleIcon = document.querySelector('.toggle-icon');
        if (toggleIcon) {
            toggleIcon.textContent = isVisible ? '▼' : '▲';
        }
    }
    
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleTemplatesGrid);
    }
    
    // Close grid when clicking outside
    document.addEventListener('click', function(event) {
        if (!templatesContainer.contains(event.target)) {
            templatesPanel.style.display = 'none';
            
            // Update toggle icon
            const toggleIcon = document.querySelector('.toggle-icon');
            if (toggleIcon) {
                toggleIcon.textContent = '▼';
            }
        }
    });
    
    // Select "Creative" template by default (or whichever you prefer)
    const defaultTemplate = Array.from(templatesGrid.querySelectorAll('.template-option'))
        .find(template => template.dataset.templateId === 'creative'); // Change 'creative' to any default
    
    if (defaultTemplate) {
        defaultTemplate.classList.add('selected');
        window.selectedTemplateId = defaultTemplate.dataset.templateId;
    } else {
        // Fallback to first template
        const firstTemplate = templatesGrid.querySelector('.template-option');
        if (firstTemplate) {
            firstTemplate.classList.add('selected');
            window.selectedTemplateId = firstTemplate.dataset.templateId;
        }
    }
    
    console.log('[templates.js] Finished adding all templates');
}
// Add this function to templates.js
function initializeCleanTemplateSelector() {
    const container = document.getElementById('templates-container-clean');
    if (!container) return;

    // Create simple dropdown for templates
    const dropdown = document.createElement('div');
    dropdown.className = 'template-dropdown-clean';
    
    dropdown.innerHTML = `
        <div class="template-selected-clean" onclick="toggleTemplateDropdown()">
            <div style="display: flex; align-items: center;">
                <div class="template-preview-mini" style="background: linear-gradient(135deg, #ff6b6b, #4ecdc4);"></div>
                Creative
            </div>
            <i class="fas fa-chevron-down"></i>
        </div>
        <div class="template-options-clean hidden" id="template-options">
            ${templates.map(template => `
                <div class="template-option-clean" data-template-id="${template.id}">
                    <div class="template-preview-mini" style="background: ${template.colors.primary};"></div>
                    <span>${template.name}</span>
                </div>
            `).join('')}
        </div>
    `;
    
    container.appendChild(dropdown);
}

function toggleTemplateDropdown() {
    const options = document.getElementById('template-options');
    if (options) {
        options.classList.toggle('hidden');
    }
}
// Make sure we only initialize once
document.addEventListener('DOMContentLoaded', function() {
    console.log('[templates.js] DOMContentLoaded event in templates.js');
    // Don't call initializeTemplateSelector() here - let editor.js handle it
});

// In layouts.js, add logging to the initializeTemplates function
function initializeTemplates() {
    console.log('[layouts.js] initializeTemplates called');
    const templatesContainer = document.getElementById('templates-container');
    
    if (!templatesContainer) {
        console.error('[layouts.js] Templates container not found');
        return;
    }
    
    console.log('[layouts.js] Current content of templates container:', templatesContainer.innerHTML);
    
    // Clear any existing content
    templatesContainer.innerHTML = '';
    console.log('[layouts.js] Cleared templates container');
    
    // Add each template option
    templates.forEach((template, index) => {
        console.log(`[layouts.js] Adding template ${index + 1}/${templates.length}: ${template.id}`);
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
            console.log(`[layouts.js] Template selected: ${template.id}`);
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
        console.log('[layouts.js] Selected first template by default');
        firstTemplate.classList.add('selected');
    }
    console.log('[layouts.js] Finished template initialization');
}

// Function to get a template by ID
function getTemplateById(templateId) {
    return templates.find(template => template.id === templateId);
}

// Initialize templates when the DOM is loaded
document.addEventListener('DOMContentLoaded', initializeTemplateSelector);

// Make functions available globally
window.getTemplateById = getTemplateById;