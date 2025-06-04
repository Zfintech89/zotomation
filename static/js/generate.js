// generate.js - New generation flow with outline → theme → slides

document.addEventListener('DOMContentLoaded', function() {
    initializeGeneratePage();
});

function initializeGeneratePage() {
    const method = window.generateState.method;
    
    // Set up the page based on method
    setupMethodDisplay(method);
    setupEventListeners();
    setupInputValidation();
    loadThemes();
    
    console.log(`🎯 Initialized generate page for method: ${method}`);
}

function setupMethodDisplay(method) {
    // Hide all panels first
    document.querySelectorAll('.input-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    
    // Show the correct panel
    const panelMap = {
        'topic': 'topic-panel',
        'text': 'text-panel', 
        'upload': 'upload-panel'
    };
    
    const activePanel = document.getElementById(panelMap[method]);
    if (activePanel) {
        activePanel.style.display = 'block';
    }
    
    // Update method indicator
    const methodBadge = document.getElementById('method-badge');
    const methodName = document.getElementById('method-name');
    
    const methodInfo = {
        'topic': { icon: 'fas fa-lightbulb', name: 'Generate from Topic' },
        'text': { icon: 'fas fa-file-text', name: 'Generate from Text' },
        'upload': { icon: 'fas fa-file-upload', name: 'Generate from Document' }
    };
    
    if (methodInfo[method]) {
        methodBadge.querySelector('i').className = methodInfo[method].icon;
        methodName.textContent = methodInfo[method].name;
    }
    
    // Update button text
    updateGenerateButtonText(method);
}

function setupEventListeners() {
    const method = window.generateState.method;
    
    // Generate outline button
    const generateBtn = document.getElementById('generate-outline-btn');
    generateBtn.addEventListener('click', handleGenerateOutline);
    
    // Outline actions
    document.getElementById('approve-outline-btn')?.addEventListener('click', handleApproveOutline);
    document.getElementById('regenerate-outline-btn')?.addEventListener('click', handleRegenerateOutline);
    document.getElementById('back-to-input-btn')?.addEventListener('click', () => showSection('input'));
    
    // Theme actions
    document.getElementById('create-slides-btn')?.addEventListener('click', handleCreateSlides);
    document.getElementById('back-to-outline-btn')?.addEventListener('click', () => showSection('outline'));
    
    // Method-specific listeners
    if (method === 'topic') {
        setupTopicListeners();
    } else if (method === 'text') {
        setupTextListeners();
    } else if (method === 'upload') {
        setupUploadListeners();
    }
}

function setupTopicListeners() {
    const topicInput = document.getElementById('topic-input');
    const slideCountInput = document.getElementById('slide-count');
    
    topicInput.addEventListener('input', validateTopicInput);
    slideCountInput.addEventListener('change', validateTopicInput);
    
    // Enter key to generate
    topicInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !document.getElementById('generate-outline-btn').disabled) {
            handleGenerateOutline();
        }
    });
}

function setupTextListeners() {
    const textInput = document.getElementById('text-input');
    const topicInput = document.getElementById('text-topic');
    
    textInput.addEventListener('input', function() {
        updateTextStats();
        validateTextInput();
    });
    
    textInput.addEventListener('paste', function() {
        setTimeout(() => {
            updateTextStats();
            validateTextInput();
        }, 10);
    });
    
    topicInput.addEventListener('input', validateTextInput);
}

function setupUploadListeners() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const topicInput = document.getElementById('upload-topic');
    
    fileInput.addEventListener('change', handleFileUpload);
    topicInput.addEventListener('input', validateUploadInput);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload();
        }
    });
    
    // Processing mode selection
    document.querySelectorAll('.processing-mode').forEach(mode => {
        mode.addEventListener('click', function() {
            document.querySelectorAll('.processing-mode').forEach(m => m.classList.remove('selected'));
            this.classList.add('selected');
            validateUploadInput();
        });
    });
}

function setupInputValidation() {
    // Real-time validation for all methods
    setInterval(function() {
        const method = window.generateState.method;
        let isValid = false;
        
        if (method === 'topic') {
            isValid = validateTopicInput();
        } else if (method === 'text') {
            isValid = validateTextInput();
        } else if (method === 'upload') {
            isValid = validateUploadInput();
        }
        
        document.getElementById('generate-outline-btn').disabled = !isValid;
    }, 500);
}

// Validation functions
function validateTopicInput() {
    const topic = document.getElementById('topic-input').value.trim();
    const slideCount = parseInt(document.getElementById('slide-count').value);
    
    const isValid = topic.length >= 5 && slideCount >= 3 && slideCount <= 10;
    
    if (isValid) {
        window.generateState.inputData = {
            topic: topic,
            slideCount: slideCount
        };
    }
    
    return isValid;
}

function validateTextInput() {
    const text = document.getElementById('text-input').value.trim();
    const topic = document.getElementById('text-topic').value.trim();
    
    const isValid = text.length >= 100; // Minimum text length
    
    if (isValid) {
        window.generateState.inputData = {
            text: text,
            topic: topic || extractTopicFromText(text),
            method: 'text'
        };
    }
    
    return isValid;
}

function validateUploadInput() {
    const filePreview = document.getElementById('file-preview');
    const topic = document.getElementById('upload-topic').value.trim();
    const selectedMode = document.querySelector('.processing-mode.selected');
    
    const hasFile = !filePreview.classList.contains('hidden');
    const hasProcessingMode = selectedMode !== null;
    
    const isValid = hasFile && hasProcessingMode;
    
    if (isValid) {
        window.generateState.inputData = {
            topic: topic || 'Document Presentation',
            processingMode: selectedMode.dataset.mode,
            method: 'upload',
            hasFile: true
        };
    }
    
    return isValid;
}

// Text statistics
function updateTextStats() {
    const text = document.getElementById('text-input').value;
    const charCount = text.length;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    // Estimate slides based on headings and content length
    const headings = (text.match(/^#{1,3}\s+.+$/gm) || []).length;
    let estimatedSlides = Math.max(headings, Math.ceil(wordCount / 200));
    estimatedSlides = Math.min(10, Math.max(3, estimatedSlides));
    
    document.getElementById('text-char-count').textContent = `${charCount.toLocaleString()} characters`;
    document.getElementById('text-word-count').textContent = `${wordCount.toLocaleString()} words`;
    document.getElementById('text-estimated-slides').textContent = `Estimated: ${estimatedSlides} slides`;
}

function extractTopicFromText(text) {
    const lines = text.split('\\n');
    const firstLine = lines[0]?.trim();
    
    if (firstLine && firstLine.length < 100 && !firstLine.endsWith('.')) {
        return firstLine.replace(/^#+\\s*/, ''); // Remove markdown headers
    }
    
    const words = text.split(' ').slice(0, 5).join(' ');
    return words.length > 50 ? words.substring(0, 50) + '...' : words;
}

// File upload handling
async function handleFileUpload() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    console.log('📁 File selected:', file.name);
    
    // Validate file type and size
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExt)) {
        showNotification('Please upload a PDF, DOCX, DOC, or TXT file.', 'error');
        clearFile();
        return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
        showNotification('File size must be less than 50MB.', 'error');
        clearFile();
        return;
    }
    
    // Show file preview
    showFilePreview(file);
    
    try {
        // Process the file
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/process-document', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Document processing failed');
        }
        
        console.log('✅ Document processed successfully:', result);
        
        // Update file preview with results
        updateFilePreview(result);
        
        // Show processing mode selection
        document.getElementById('processing-mode-container').classList.remove('hidden');
        
        // Store processed content
        window.generateState.processedContent = result.content;
        
        showNotification('Document processed successfully! Choose processing mode below.', 'success');
        
    } catch (error) {
        console.error('❌ Document processing error:', error);
        showNotification(error.message || 'Failed to process document', 'error');
        clearFile();
    }
}

function showFilePreview(file) {
    const preview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const fileStats = document.getElementById('file-stats');
    const fileIcon = document.getElementById('file-icon');
    
    // Update file info
    fileName.textContent = file.name;
    fileStats.textContent = 'Processing...';
    
    // Update icon based on file type
    const extension = file.name.split('.').pop().toLowerCase();
    let iconClass = 'fas fa-file';
    
    switch (extension) {
        case 'pdf':
            iconClass = 'fas fa-file-pdf';
            break;
        case 'docx':
        case 'doc':
            iconClass = 'fas fa-file-word';
            break;
        case 'txt':
            iconClass = 'fas fa-file-alt';
            break;
    }
    
    fileIcon.innerHTML = `<i class="${iconClass}"></i>`;
    preview.classList.remove('hidden');
}

function updateFilePreview(result) {
    const fileStats = document.getElementById('file-stats');
    const stats = result.stats;
    
    fileStats.textContent = `${stats.words.toLocaleString()} words • ${stats.characters.toLocaleString()} characters • Ready for processing`;
}

function clearFile() {
    const fileInput = document.getElementById('file-input');
    const preview = document.getElementById('file-preview');
    const processingContainer = document.getElementById('processing-mode-container');
    
    fileInput.value = '';
    preview.classList.add('hidden');
    processingContainer.classList.add('hidden');
    
    delete window.generateState.processedContent;
    validateUploadInput();
}

// Slide count adjustment
function adjustSlideCount(delta) {
    const input = document.getElementById('slide-count');
    let value = parseInt(input.value) + delta;
    value = Math.max(3, Math.min(10, value));
    input.value = value;
    validateTopicInput();
}

function updateGenerateButtonText(method) {
    const button = document.getElementById('generate-outline-btn');
    const buttonText = document.getElementById('generate-btn-text');
    
    const texts = {
        'topic': 'Generate Outline',
        'text': 'Analyze Text & Create Outline',
        'upload': 'Process Document & Create Outline'
    };
    
    buttonText.textContent = texts[method] || 'Generate Outline';
}

// Outline generation
async function handleGenerateOutline() {
    const method = window.generateState.method;
    
    if (window.generateState.processing) return;
    
    console.log(`🎯 Generating outline for method: ${method}`);
    
    // Show loading
    showSection('outline');
    showOutlineLoading(true);
    
    window.generateState.processing = true;
    
    try {
        let requestData = {
            inputMethod: method,
            slideCount: method === 'topic' ? window.generateState.inputData.slideCount : undefined
        };
        
        if (method === 'topic') {
            requestData.topic = window.generateState.inputData.topic;
            
        } else if (method === 'text') {
            requestData.topic = window.generateState.inputData.topic;
            requestData.textContent = window.generateState.inputData.text;
            requestData.textStats = {
                words: window.generateState.inputData.text.split(' ').length,
                characters: window.generateState.inputData.text.length
            };
            
        } else if (method === 'upload') {
            requestData.topic = window.generateState.inputData.topic;
            requestData.documentContent = window.generateState.processedContent.full_text;
            requestData.documentStats = window.generateState.processedContent.analysis;
            requestData.processingMode = window.generateState.inputData.processingMode;
        }
        
        const response = await fetch('/api/generate-outline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to generate outline');
        }
        
        console.log('✅ Outline generated successfully:', result);
        
        // Store outline
        window.generateState.outline = result.outline;
        
        // Display outline
        displayOutline(result.outline);
        showOutlineLoading(false);
        
        // Update step progress
        updateStepProgress('outline');
        
    } catch (error) {
        console.error('❌ Error generating outline:', error);
        showNotification(error.message || 'Failed to generate outline', 'error');
        showSection('input');
    } finally {
        window.generateState.processing = false;
    }
}

function showOutlineLoading(show) {
    const loading = document.getElementById('outline-loading');
    const content = document.getElementById('outline-content');
    const actions = document.getElementById('outline-actions');
    
    if (show) {
        loading.classList.remove('hidden');
        content.classList.add('hidden');
        actions.classList.add('hidden');
        
        // Update loading message based on method
        const method = window.generateState.method;
        const messages = {
            'topic': 'Analyzing your topic and creating the perfect presentation structure...',
            'text': 'Analyzing your text content and organizing it into a coherent presentation flow...',
            'upload': 'Processing your document and extracting key insights for a structured presentation...'
        };
        
        document.getElementById('outline-loading-message').textContent = messages[method];
    } else {
        loading.classList.add('hidden');
        content.classList.remove('hidden');
        actions.classList.remove('hidden');
    }
}

function displayOutline(outline) {
    const container = document.getElementById('outline-content');
    const slides = outline.slide_structure || [];
    const meta = outline.presentation_meta || {};
    
    let slidesHtml = '';
    slides.forEach((slide, index) => {
        const keyPointsHtml = slide.key_points ? 
            slide.key_points.map(point => `<li>${point}</li>`).join('') : '';
        
        slidesHtml += `
            <div class="outline-slide-card">
                <div class="slide-header">
                    <div class="slide-number">${slide.slide_number}</div>
                    <div class="slide-info">
                        <h4>${slide.title}</h4>
                        <div class="slide-meta">
                            <span class="layout-badge">${getLayoutDisplayName(slide.layout)}</span>
                            <span class="purpose-text">${slide.purpose}</span>
                        </div>
                    </div>
                </div>
                <div class="slide-details">
                    <p class="slide-context">${slide.context}</p>
                    ${keyPointsHtml ? `
                        <div class="key-points">
                            <strong>Key Points:</strong>
                            <ul>${keyPointsHtml}</ul>
                        </div>
                    ` : ''}
                    <div class="transitions">
                        ${slide.transitions.from_previous ? 
                            `<div class="transition from">← ${slide.transitions.from_previous}</div>` : ''}
                        ${slide.transitions.to_next ? 
                            `<div class="transition to">${slide.transitions.to_next} →</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = `
        <div class="outline-summary">
            <h3>${meta.title || 'Presentation Outline'}</h3>
            <div class="meta-info">
                <div class="meta-item">
                    <strong>Objective:</strong> <span>${meta.objective || 'Comprehensive overview'}</span>
                </div>
                <div class="meta-item">
                    <strong>Target Audience:</strong> <span>${meta.target_audience || 'General audience'}</span>
                </div>
                <div class="meta-item">
                    <strong>Key Message:</strong> <span>${meta.key_message || 'Main insights and takeaways'}</span>
                </div>
            </div>
        </div>
        
        <div class="outline-slides">
            <h4>Planned Slide Structure (${slides.length} slides)</h4>
            <div class="slides-flow">
                ${slidesHtml}
            </div>
        </div>
    `;
}

function getLayoutDisplayName(layoutId) {
    const layoutNames = {
        'titleOnly': 'Title Slide',
        'titleAndBullets': 'Bullets',
        'imageAndParagraph': 'Image + Text',
        'twoColumn': 'Two Columns',
        'quote': 'Quote',
        'timeline': 'Timeline',
        'conclusion': 'Conclusion',
        'imageWithFeatures': 'Features',
        'numberedFeatures': 'Numbered',
        'benefitsGrid': 'Benefits',
        'iconGrid': 'Icon Grid',
        'sideBySideComparison': 'Comparison'
    };
    
    return layoutNames[layoutId] || layoutId;
}

// Outline actions
function handleApproveOutline() {
    if (!window.generateState.outline) {
        showNotification('No outline available', 'error');
        return;
    }
    
    console.log('✅ Outline approved, proceeding to theme selection');
    showSection('theme');
    updateStepProgress('theme');
}

async function handleRegenerateOutline() {
    console.log('🔄 Regenerating outline...');
    showOutlineLoading(true);
    
    try {
        // Add slight delay to show user action was registered
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Call the same generation function
        await handleGenerateOutline();
        
    } catch (error) {
        console.error('❌ Error regenerating outline:', error);
        showNotification('Failed to regenerate outline', 'error');
        showOutlineLoading(false);
    }
}

// Theme selection
function loadThemes() {
    const themeGrid = document.getElementById('theme-grid');
    
    // Define available themes (matching your templates.js)
    const themes = [
        { id: 'corporate', name: 'Corporate', colors: { primary: '#0f4c81', secondary: '#6e9cc4', accent: '#f2b138' } },
        { id: 'creative', name: 'Creative', colors: { primary: '#ff6b6b', secondary: '#4ecdc4', accent: '#ffd166' } },
        { id: 'minimal', name: 'Minimal', colors: { primary: '#2c3e50', secondary: '#95a5a6', accent: '#e74c3c' } },
        { id: 'nature', name: 'Nature', colors: { primary: '#2d6a4f', secondary: '#74c69d', accent: '#ffb703' } },
        { id: 'tech', name: 'Tech', colors: { primary: '#3a0ca3', secondary: '#4361ee', accent: '#7209b7' } },
        { id: 'gradient', name: 'Gradient', colors: { primary: '#8338ec', secondary: '#3a86ff', accent: '#ff006e' } },
        { id: 'energetic', name: 'Energetic', colors: { primary: '#f72585', secondary: '#7209b7', accent: '#4cc9f0' } },
        { id: 'earthy', name: 'Earthy', colors: { primary: '#996633', secondary: '#dda15e', accent: '#bc6c25' } }
    ];
    
    let themesHtml = '';
    themes.forEach(theme => {
        themesHtml += `
            <div class="theme-card" data-theme="${theme.id}">
                <div class="theme-preview">
                    <div class="theme-colors">
                        <div class="color-bar" style="background-color: ${theme.colors.primary}"></div>
                        <div class="color-bar" style="background-color: ${theme.colors.secondary}"></div>
                        <div class="color-bar" style="background-color: ${theme.colors.accent}"></div>
                    </div>
                    <div class="theme-sample">
                        <div class="sample-title" style="color: ${theme.colors.primary}">Sample Title</div>
                        <div class="sample-content" style="color: ${theme.colors.secondary}">
                            <div class="sample-bullet" style="border-left-color: ${theme.colors.accent}">Key Point</div>
                            <div class="sample-bullet" style="border-left-color: ${theme.colors.accent}">Another Point</div>
                        </div>
                    </div>
                </div>
                <div class="theme-name">${theme.name}</div>
            </div>
        `;
    });
    
    themeGrid.innerHTML = themesHtml;
    
    // Add click listeners
    document.querySelectorAll('.theme-card').forEach(card => {
        card.addEventListener('click', function() {
            // Remove previous selection
            document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
            
            // Select this theme
            this.classList.add('selected');
            window.generateState.selectedTheme = this.dataset.theme;
            
            // Enable create button
            document.getElementById('create-slides-btn').disabled = false;
            
            console.log('🎨 Theme selected:', window.generateState.selectedTheme);
        });
    });
}

// Final slide generation
async function handleCreateSlides() {
    if (!window.generateState.outline || !window.generateState.selectedTheme) {
        showNotification('Missing outline or theme selection', 'error');
        return;
    }
    
    console.log('🎨 Creating slides with theme:', window.generateState.selectedTheme);
    
    // Show generation section
    showSection('generation');
    updateStepProgress('generate');
    
    try {
        const requestData = {
            outline: window.generateState.outline,
            template: window.generateState.selectedTheme
        };
        
        // Add content data if available
        if (window.generateState.method === 'text' || window.generateState.method === 'upload') {
            requestData.contentData = window.generateState.processedContent;
            requestData.processingMode = window.generateState.inputData.processingMode || 'preserve';
        }
        
        updateGenerationProgress(20, 'Generating slides from outline...');
        
        const response = await fetch('/api/generate-from-outline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        updateGenerationProgress(70, 'Processing slide content...');
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to generate slides');
        }
        
        updateGenerationProgress(100, 'Finalizing presentation...');
        
        console.log('✅ Slides generated successfully:', result);
        
        // Small delay to show completion
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Navigate to editor with the generated slides
        navigateToEditor(result);
        
    } catch (error) {
        console.error('❌ Error generating slides:', error);
        showNotification(error.message || 'Failed to generate slides', 'error');
        
        // Go back to theme selection
        showSection('theme');
        updateStepProgress('theme');
    }
}

function updateGenerationProgress(percentage, message) {
    const progressFill = document.getElementById('generation-progress-fill');
    const progressText = document.getElementById('generation-progress-text');
    
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = message;
    
    // Update stages
    if (percentage >= 100) {
        document.getElementById('stage-complete').classList.add('active');
    }
}

// Fix in generate.js - Update the navigateToEditor function
function navigateToEditor(result) {
    // Store the generated data in sessionStorage for the editor
    const editorData = {
        slides: result.slides,
        template: result.template,
        topic: window.generateState.outline.presentation_meta?.title || 'Generated Presentation',
        generationMethod: window.generateState.method,
        outline: window.generateState.outline,
        timestamp: new Date().toISOString(),
        isNewGeneration: true
    };
    
    try {
        sessionStorage.setItem('generatedPresentation', JSON.stringify(editorData));
        console.log('✅ Stored generated presentation data:', editorData);
    } catch (e) {
        console.warn('Could not store data in sessionStorage:', e);
    }
    
    // Navigate to editor with flag
    window.location.href = '/editor?generated=true';
}

// Add this helper function to generate.js for debugging
function debugGeneratedData() {
    const stored = sessionStorage.getItem('generatedPresentation');
    if (stored) {
        console.log('📱 Generated data in storage:', JSON.parse(stored));
    } else {
        console.log('❌ No generated data found in storage');
    }
}

// Section navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.input-section, .outline-section, .theme-section, .generation-section').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show target section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }
    
    window.generateState.currentStep = sectionName;
}

function updateStepProgress(currentStep) {
    const steps = ['input', 'outline', 'theme', 'generate'];
    const currentIndex = steps.indexOf(currentStep);
    
    steps.forEach((step, index) => {
        const stepElement = document.getElementById(`step-${step}`);
        if (stepElement) {
            if (index <= currentIndex) {
                stepElement.classList.add('active');
            } else {
                stepElement.classList.remove('active');
            }
        }
    });
}

// Utility functions
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.getElementById('notification');
    if (!notification) {
        console.log(`${type.toUpperCase()}: ${message}`);
        return;
    }
    
    const notificationMessage = notification.querySelector('.notification-message');
    const notificationIcon = notification.querySelector('.notification-icon');
    
    // Set message
    if (notificationMessage) {
        notificationMessage.textContent = message;
    }
    
    // Set icon and styling based on type
    if (notificationIcon) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        notificationIcon.className = `notification-icon ${icons[type] || icons.info}`;
    }
    
    // Apply type-specific styling
    notification.className = `notification ${type} show`;
    
    // Auto-hide after duration
    setTimeout(() => {
        notification.classList.remove('show');
    }, duration);
}

// Global functions for HTML onclick handlers
window.adjustSlideCount = adjustSlideCount;
window.clearFile = clearFile;