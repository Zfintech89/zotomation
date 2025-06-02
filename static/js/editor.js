document.addEventListener('DOMContentLoaded', function() {
    const templatesContainer = document.getElementById('templates-container');
    console.log('[editor.js] Templates container found:', !!templatesContainer);
    // if (templatesContainer) {
    //     console.log('[editor.js] Templates container already has content:', !!templatesContainer.querySelector('.template-card'));
    //     console.log('[editor.js] Current templates container HTML:', templatesContainer.innerHTML);
    // }
        if (!window.inputMethodsHandler) {
        window.inputMethodsHandler = new InputMethodsHandler();
    }
    const topicInput = document.getElementById('topic');
    const slideCountInput = document.getElementById('slide-count');
    const generateBtn = document.getElementById('generate-btn');
    const exportBtn = document.getElementById('export-btn');
    const saveBtn = document.getElementById('save-btn');
    const slidePreview = document.getElementById('slide-preview');
    const loadingIndicator = document.getElementById('loading');
    const slidesList = document.getElementById('slides-list');
    const slidesControls = document.getElementById('slide-controls');
    const editControlsContainer = document.getElementById('external-edit-controls');
    const editSlideBtn = document.getElementById('edit-slide-btn');
     const methodTabs = document.querySelectorAll('.method-tab');
    methodTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const method = this.dataset.method;
            
            // Dispatch custom event
            const event = new CustomEvent('input-method-changed', {
                detail: { method: method }
            });
            document.dispatchEvent(event);
        });
    });
    window.appState = {
        slides: [],
        templateId: null,
        topic: null,
        currentSlideIndex: 0,
        editMode: false,
        presentationId: null,
        isModified: false,
        isGenerating: false // New flag to track generation status
    };
    
    if (generateBtn) {
document.addEventListener('input-method-changed', function(e) {
    const method = e.detail.method;
    
    // Update button text
    const buttonTexts = {
        topic: '<i class="fas fa-magic"></i> Generate Presentation',
        text: '<i class="fas fa-file-text"></i> Generate from Text (AI Auto-Count)',
        document: '<i class="fas fa-file-upload"></i> Generate from Document (AI Auto-Count)'
    };
    
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.innerHTML = buttonTexts[method] || buttonTexts.topic;
    }
    
    // Update UI for slide count
    updateUIForInputMethod(method);
});
    }

    // Add beforeunload event listener
    window.addEventListener('beforeunload', function(e) {
        if (window.appState.isGenerating) {
            e.preventDefault();
            e.returnValue = 'Presentation is currently being generated. Are you sure you want to leave? This will interrupt the generation process.';
            return e.returnValue;
        }
    });

    if (window.existingPresentation) {
        initializeWithExistingPresentation(window.existingPresentation);
    }

    initializeTemplateSelector();
    
    generateBtn.addEventListener('click', handleGenerate);
    exportBtn.addEventListener('click', handleExport);
    saveBtn.addEventListener('click', handleSave);
    

    if (editSlideBtn) {
        editSlideBtn.addEventListener('click', showEditForm);
    }
    
function initializeWithExistingPresentation(presentation) {
    console.log('🔄 Initializing with existing presentation:', presentation);
    
    if (!presentation || !presentation.id) {
        console.error('Invalid presentation data');
        return;
    }
    
    // Set application state
    appState.presentationId = presentation.id;
    appState.topic = presentation.topic || 'Untitled';
    appState.templateId = presentation.template_id || 'corporate';
    appState.slides = presentation.slides.map(slide => ({
        layout: slide.layout,
        content: slide.content
    }));
    
    // Update form fields
    document.getElementById('topic').value = appState.topic;
    const slideCountInput = document.getElementById('slide-count');
    if (slideCountInput) {
        slideCountInput.value = appState.slides.length;
    }
    
    // Set template selection
    setTimeout(() => {
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('selected');
            if (card.dataset.id === appState.templateId) {
                card.classList.add('selected');
                window.selectedTemplateId = appState.templateId;
            }
        });
        
        // Enable buttons and render
        document.getElementById('export-btn').disabled = false;
        document.getElementById('save-btn').disabled = false;
        
        renderSlidesList();
        renderCurrentSlide();
        updateSaveButtonLabel();
        
        console.log(' Presentation loaded successfully');
    }, 100);
}


// 1. UPDATE: generateFromProcessedContent function - REMOVE slideCount parameter
async function generateFromProcessedContent(content, method) {
    const topicInput = document.getElementById('topic');
    // REMOVED: const slideCount = parseInt(slideCountInput.value, 10) || content.analysis?.suggested_slides || 5;
    const topic = topicInput.value.trim() || extractTopicFromContent(content) || 'Presentation';
    
    console.log('Generating slides:', {
        method,
        // REMOVED: slideCount,
        topic,
        contentLength: content.full_text?.length || 0,
        message: 'Ollama will determine optimal slide count'
    });
    
    const response = await fetch('/api/generate-from-content', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: content,
            template: window.selectedTemplateId,
            // REMOVED: slideCount: slideCount,
            topic: topic
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Content generation failed: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Add metadata about the generation method
    result.generationMethod = method;
    result.contentStats = content.analysis;
    
    // Log Ollama's analysis results

    
    console.log('Generated slides successfully:', result);
    
    return result;
}

// 3. UPDATE: validateInputs function - Make slide count optional for document/text methods
function validateInputs() {
    const inputMethod = window.inputMethodsHandler?.getCurrentMethod() || 'topic';
    
    // Validate based on input method
    if (window.inputMethodsHandler) {
        const validation = window.inputMethodsHandler.validateCurrentInput();
        if (!validation.valid) {
            showNotification(validation.message, 'error');
            return false;
        }
    }
    
    // Validate template selection
    if (!window.selectedTemplateId) {
        showNotification('Please select a template', 'error');
        return false;
    }
    
    // Validate slide count ONLY for topic-based generation
    if (inputMethod === 'topic') {
        const slideCountInput = document.getElementById('slide-count');
        if (slideCountInput) {
            const slideCount = parseInt(slideCountInput.value, 10);
            if (isNaN(slideCount) || slideCount < 1 || slideCount > 10) {
                showNotification('Please enter a valid slide count (1-10)', 'error');
                return false;
            }
        }
    }
    // For document/text methods, slide count is determined by Ollama
    
    return true;
}

// 4. NEW FUNCTION: Show Ollama analysis results to user
// function showOllamaAnalysisResults(analysis) {
//     // Remove any existing analysis display
//     const existingAnalysis = document.getElementById('ollama-analysis-display');
//     if (existingAnalysis) {
//         existingAnalysis.remove();
//     }
    
//     // Create analysis display
//     const analysisDiv = document.createElement('div');
//     analysisDiv.id = 'ollama-analysis-display';
//     analysisDiv.className = 'ollama-analysis-card';
//     analysisDiv.innerHTML = `
//         <div class="analysis-header">
//             <h4><i class="fas fa-robot"></i> AI Analysis Results</h4>
//             <button class="close-analysis" onclick="this.parentElement.parentElement.remove()">×</button>
//         </div>
//         <div class="analysis-content">
//             <div class="analysis-stat">
//                 <strong>Slides Generated:</strong> 
//                 <span class="highlight">${analysis.determined_slide_count}</span>
//             </div>
//             <div class="analysis-reasoning">
//                 <strong>AI Reasoning:</strong> 
//                 <p>${analysis.reasoning}</p>
//             </div>
//             <div class="analysis-status">
//                 <strong>Analysis Status:</strong> 
//                 <span class="${analysis.structure_success ? 'success' : 'warning'}">
//                     ${analysis.structure_success ? '✅ AI Structure Analysis' : '⚠️ Fallback Analysis Used'}
//                 </span>
//             </div>
//         </div>
//     `;
    
//     // Insert after the slides container or at the top of the main content
//     const slidesContainer = document.getElementById('slides-container');
//     const mainContent = document.querySelector('.main-content') || document.body;
    
//     if (slidesContainer && slidesContainer.parentNode) {
//         slidesContainer.parentNode.insertBefore(analysisDiv, slidesContainer.nextSibling);
//     } else {
//         mainContent.insertBefore(analysisDiv, mainContent.firstChild);
//     }
    
//     // Auto-hide after 10 seconds
//     setTimeout(() => {
//         if (analysisDiv.parentNode) {
//             analysisDiv.remove();
//         }
//     }, 10000);
// }

// 5. UPDATE: Hide/show slide count input based on method
function updateUIForInputMethod(method) {
    const slideCountContainer = document.getElementById('slide-count-container') || 
                               document.querySelector('.slide-count-group') ||
                               document.getElementById('slide-count')?.parentElement;
    
    if (method === 'document' || method === 'text') {
        // Hide slide count input - Ollama will decide
        if (slideCountContainer) {
            slideCountContainer.style.display = 'none';
        }
        
        // Show info message
        showAutoSlideCountMessage();
    } else {
        // Show slide count input for topic-based generation
        if (slideCountContainer) {
            slideCountContainer.style.display = 'block';
        }
        
        // Hide info message
        hideAutoSlideCountMessage();
    }
}

// 6. NEW FUNCTION: Show auto slide count message
// function showAutoSlideCountMessage() {
//     // Remove existing message
//     const existingMessage = document.getElementById('auto-slide-message');
//     if (existingMessage) {
//         existingMessage.remove();
//     }
    
//     // Create info message
//     const infoDiv = document.createElement('div');
//     infoDiv.id = 'auto-slide-message';
//     infoDiv.className = 'auto-slide-info';
//     infoDiv.innerHTML = `
//         <div class="info-card">
//             <i class="fas fa-robot"></i>
//             <span>AI will automatically determine the optimal number of slides based on your content.</span>
//         </div>
//     `;
    
//     // Insert after slide count container or before generate button
//     const generateBtn = document.getElementById('generate-btn');
//     const slideCountContainer = document.getElementById('slide-count-container');
    
//     if (slideCountContainer && slideCountContainer.parentNode) {
//         slideCountContainer.parentNode.insertBefore(infoDiv, slideCountContainer.nextSibling);
//     } else if (generateBtn && generateBtn.parentNode) {
//         generateBtn.parentNode.insertBefore(infoDiv, generateBtn);
//     }
// }

// // 7. NEW FUNCTION: Hide auto slide count message
// function hideAutoSlideCountMessage() {
//     const autoMessage = document.getElementById('auto-slide-message');
//     if (autoMessage) {
//         autoMessage.remove();
//     }
// }
async function generateFromDocument() {
    const processedContent = window.inputMethodsHandler.getProcessedContent();

    if (!processedContent) {
        throw new Error('No processed document content available. Please upload a document first.');
    }

    console.log('Generating from document with processed content:', processedContent);

    return await generateFromProcessedContent(processedContent, 'document');
}


// Helper function: Generate from topic only (no changes needed)
async function generateFromTopicOnly() {
    const topicInput = document.getElementById('topic');
    const slideCountInput = document.getElementById('slide-count');
    const topic = topicInput.value.trim();
    const slideCount = parseInt(slideCountInput.value, 10) || 5;
    
    if (!topic) {
        throw new Error('Please enter a presentation topic');
    }
    
    console.log('Generating from topic only:', { topic, slideCount, template: window.selectedTemplateId });
    
    const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            template: window.selectedTemplateId,
            topic: topic,
            slideCount: slideCount
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error: ${response.status}`);
    }
    
    return await response.json();
}

// Helper function: Generate from text only (UPDATED)
async function generateFromTextOnly() {
    const textContent = window.inputMethodsHandler.getTextContent();
    
    if (!textContent) {
        throw new Error('Please paste some text content');
    }
    
    if (textContent.length < 50) {
        throw new Error('Please provide more text content (at least 50 characters)');
    }
    
    const processingMode = 'preserve'; // Default for text
    
    console.log('Processing text content for generation:', {
        textLength: textContent.length,
        processingMode: processingMode,
        method: 'text-only'
    });
    
    try {
        // Process the text content first
        const result = await window.inputMethodsHandler.processTextContent();
        
        // Generate slides from processed content with processing mode
        return await generateFromProcessedContentOnly(result.content, 'text', processingMode);
        
    } catch (error) {
        throw new Error(`Text processing failed: ${error.message}`);
    }
}

// Helper function: Generate from document only (UPDATED)
async function generateFromDocumentOnly() {
    const processedContent = window.inputMethodsHandler.getProcessedContent();

    if (!processedContent) {
        throw new Error('No processed document content available. Please upload a document first.');
    }

    // Get the selected processing mode from the UI
    const processingMode = window.inputMethodsHandler.getProcessingMode();

    console.log('Generating from document only with processed content:', {
        hasContent: !!processedContent,
        contentKeys: Object.keys(processedContent),
        processingMode: processingMode,
        method: 'document-only'
    });

    return await generateFromProcessedContentOnly(processedContent, 'document', processingMode);
}

// Helper function: Generate from processed content only (UPDATED)
async function generateFromProcessedContentOnly(content, method, processingMode = 'preserve') {
    const topicInput = document.getElementById('topic');
    const topic = topicInput.value.trim() || extractTopicFromContent(content) || 'Presentation';
    
    console.log('Generating slides from processed content only:', {
        method,
        processingMode,
        topic,
        contentLength: content.full_text?.length || 0,
        message: 'Ollama will auto-determine slide count'
    });
    
    const response = await fetch('/api/generate-from-content', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: content,
            template: window.selectedTemplateId,
            topic: topic,
            processing_mode: processingMode // Send processing mode to backend
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Content generation failed: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Add metadata about the generation method
    result.generationMethod = method;
    result.contentStats = content.analysis;
    result.processingMode = processingMode;
    
    console.log('Generated slides successfully from content only:', result);
    
    return result;
}

// Helper function: Get topic from current method (no changes needed)
function getTopicFromCurrentMethod() {
    const topicInput = document.getElementById('topic');
    const inputMethod = window.inputMethodsHandler.getCurrentMethod();
    
    switch (inputMethod) {
        case 'topic':
            return topicInput.value.trim() || 'Presentation';
            
        case 'text':
            const textContent = window.inputMethodsHandler.getTextContent();
            const processedContent = window.inputMethodsHandler.getProcessedContent();
            return topicInput.value.trim() || 
                   extractTopicFromText(textContent) ||
                   extractTopicFromContent(processedContent) || 
                   'Presentation';
                   
        case 'document':
            const docProcessedContent = window.inputMethodsHandler.getProcessedContent();
            return topicInput.value.trim() || 
                   extractTopicFromContent(docProcessedContent) || 
                   'Presentation';
                   
        default:
            return 'Presentation';
    }
}

// Helper function: Extract topic from text (no changes needed)
function extractTopicFromText(text) {
    if (!text) return null;
    
    const firstLine = text.split('\n')[0].trim();
    
    if (firstLine.length < 100 && !firstLine.endsWith('.')) {
        return firstLine;
    }
    
    const words = text.split(' ').slice(0, 5).join(' ');
    return words.length > 50 ? words.substring(0, 50) + '...' : words;
}

// Helper function: Extract topic from content (no changes needed)
function extractTopicFromContent(content) {
    if (!content || !content.full_text) {
        return null;
    }
    
    const text = content.full_text;
    const firstLine = text.split('\n')[0].trim();
    
    if (firstLine.length < 100 && !firstLine.endsWith('.')) {
        return firstLine;
    }
    
    const words = text.split(' ').slice(0, 5).join(' ');
    return words.length > 50 ? words.substring(0, 50) + '...' : words;
}
async function generateFromTopic() {
    const topicInput = document.getElementById('topic');
    const slideCountInput = document.getElementById('slide-count');
    const topic = topicInput.value.trim();
    const slideCount = parseInt(slideCountInput.value, 10) || 5;
    
    if (!topic) {
        throw new Error('Please enter a presentation topic');
    }
    
    // Use existing topic-based generation
    const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            template: window.selectedTemplateId,
            topic: topic,
            slideCount: slideCount
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error: ${response.status}`);
    }
    
    return await response.json();
}

async function generateFromText() {
    try {
        // Process the text content first
        const result = await window.inputMethodsHandler.processTextContent();
        
        // Generate slides from processed content
        return await generateFromProcessedContent(result.content, 'text');
        
    } catch (error) {
        throw new Error(`Text processing failed: ${error.message}`);
    }
}

function getTopicFromMethod(method) {
    const topicInput = document.getElementById('topic');
    
    switch (method) {
        case 'topic':
            return topicInput.value.trim() || 'Presentation';
            
        case 'text':
        case 'document':
            const processedContent = window.inputMethodsHandler.getProcessedContent();
            return topicInput.value.trim() || 
                   extractTopicFromContent(processedContent) || 
                   'Presentation';
                   
        default:
            return 'Presentation';
    }
}

async function handleGenerate() {
    // Get current input method
    const inputMethod = window.inputMethodsHandler.getCurrentMethod();
    
    console.log('Starting generation with method:', inputMethod);
    
    // NEW: Get processing mode for document/text methods
    let processingMode = 'generate'; // default for topic method
    if (inputMethod === 'document') {
        processingMode = window.inputMethodsHandler.getProcessingMode();
    } else if (inputMethod === 'text') {
        processingMode = 'preserve'; // default for text method
    }
    
    console.log('Processing mode:', processingMode);
    
    // Show different loading messages based on method and processing mode
    const loadingMessages = {
        topic: 'Generating presentation...',
        text: 'Analyzing text content and preserving original structure...',
        document: `Processing document in ${processingMode} mode and determining optimal slide structure...`
    };
    
    // Validate input based on ONLY the current method
    const validation = window.inputMethodsHandler.validateCurrentInput();
    if (!validation.valid) {
        showNotification(validation.message, 'error');
        return;
    }
    
    const templateId = window.selectedTemplateId;
    if (!templateId) {
        showNotification('Please select a template', 'error');
        return;
    }
    
    // Show loading indicator with appropriate message
    const loadingIndicator = document.getElementById('loading');
    const loadingText = loadingIndicator.querySelector('p');
    if (loadingText) {
        loadingText.textContent = loadingMessages[inputMethod] || loadingMessages.topic;
    }
    
    loadingIndicator.classList.remove('hidden');
    document.getElementById('slide-preview').innerHTML = '';
    document.getElementById('external-edit-controls').classList.add('hidden');
    
    // Disable buttons during generation
    const generateBtn = document.getElementById('generate-btn');
    const exportBtn = document.getElementById('export-btn');
    const saveBtn = document.getElementById('save-btn');
    
    generateBtn.disabled = true;
    exportBtn.disabled = true;
    saveBtn.disabled = true;
    
    // Set isGenerating flag
    window.appState.isGenerating = true;
    
    try {
        let result;
        
        // Generate based on ONLY the current input method
        switch (inputMethod) {
            case 'topic':
                console.log('Generating from topic ONLY');
                result = await generateFromTopicOnly();
                break;
                
            case 'text':
                console.log('Generating from text ONLY - Preserving original content');
                result = await generateFromTextOnly();
                break;
                
            case 'document':
                console.log(`Generating from document ONLY - ${processingMode} mode`);
                result = await generateFromDocumentOnly();
                break;
                
            default:
                throw new Error('Unknown input method');
        }
        
        if (!result || !result.slides) {
            throw new Error('No slides generated');
        }
        
        // Enhanced success message with processing mode and slide count info
        let slideCountInfo = ` (${result.slides.length} slides)`;
        if (result.ollama_analysis && result.ollama_analysis.determined_slide_count) {
            slideCountInfo = ` (${result.ollama_analysis.determined_slide_count} slides determined by AI)`;
        }
        
        let processingInfo = '';
        if (inputMethod === 'document') {
            const modeLabels = {
                preserve: 'preserving original content',
                condense: 'condensing key points',
                generate: 'generating enhanced content'
            };
            processingInfo = ` - ${modeLabels[processingMode]}`;
        } else if (inputMethod === 'text') {
            processingInfo = ' - preserving original content';
        }
        
        console.log(`✅ Generated ${result.slides.length} slides using ${inputMethod} method${processingInfo}`);
        
        // Update application state
        window.appState.slides = result.slides;
        window.appState.templateId = templateId;
        window.appState.topic = getTopicFromCurrentMethod();
        window.appState.currentSlideIndex = 0;
        window.appState.editMode = false;
        window.appState.isModified = true;
        window.appState.processingMode = processingMode; // NEW: Store processing mode
        window.appState.generationMethod = inputMethod; // Store generation method
        window.appState.contentStats = result.contentStats || null; // Store content stats
        
        // Log Ollama analysis if available
        if (result.ollama_analysis) {
            console.log('📊 Ollama Analysis Results:');
            console.log(`   - Determined slide count: ${result.ollama_analysis.determined_slide_count}`);
            console.log(`   - AI reasoning: ${result.ollama_analysis.reasoning}`);
            console.log(`   - Structure analysis success: ${result.ollama_analysis.structure_success}`);
        }
        
        // Render slides
        renderSlidesList();
        renderCurrentSlide();
        
        // Enable buttons
        exportBtn.disabled = false;
        saveBtn.disabled = false;
        
        // Update save button label
        updateSaveButtonLabel();
        
        // Show detailed success notification
        const successMessage = `Presentation generated successfully${slideCountInfo}${processingInfo}!`;
        showNotification(successMessage, 'success', 7000); // Show for 7 seconds
        
        // Optional: Show additional info for document/text methods
        if (inputMethod !== 'topic' && result.contentStats) {
            setTimeout(() => {
                const statsMessage = `Content processed: ${result.contentStats.words} words, ${result.contentStats.characters} characters`;
                showNotification(statsMessage, 'info', 5000);
            }, 1000);
        }
        
    } catch (error) {
        console.error('Error generating slides:', error);
        
        // Enhanced error handling with specific messages
        let errorMessage = 'Failed to generate presentation. Please try again.';
        
        if (error.message.includes('No content')) {
            errorMessage = 'No content available. Please upload a document or enter text first.';
        } else if (error.message.includes('processing failed')) {
            errorMessage = 'Content processing failed. Please try with a different document or check file format.';
        } else if (error.message.includes('Ollama')) {
            errorMessage = 'AI content generation service is unavailable. Please try again in a moment.';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
            errorMessage = 'Network error. Please check your connection and try again.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showNotification(errorMessage, 'error', 8000); // Show error longer
        
        // Show error in preview area
        document.getElementById('slide-preview').innerHTML = `
            <div class="placeholder-message">
                <div class="error-icon" style="font-size: 3rem; color: #dc3545; margin-bottom: 1rem;">⚠️</div>
                <h3 style="color: #dc3545; margin-bottom: 1rem;">Generation Failed</h3>
                <p style="color: #6c757d; margin-bottom: 1.5rem;">${errorMessage}</p>
                <button onclick="handleGenerate()" class="btn btn-primary">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            </div>
        `;
        
    } finally {
        // Hide loading indicator and reset flags
        loadingIndicator.classList.add('hidden');
        generateBtn.disabled = false;
        window.appState.isGenerating = false;
        
        // Reset loading text to default
        if (loadingText) {
            loadingText.textContent = 'Creating your amazing presentation...';
        }
    }
}


function extractTopicFromContent(content) {
    if (!content || !content.full_text) {
        return null;
    }
    
    // Simple topic extraction from first sentence or title-like content
    const text = content.full_text;
    const firstLine = text.split('\n')[0].trim();
    
    // If first line looks like a title (short and doesn't end with period)
    if (firstLine.length < 100 && !firstLine.endsWith('.')) {
        return firstLine;
    }
    
    // Extract first few words as potential topic
    const words = text.split(' ').slice(0, 5).join(' ');
    return words.length > 50 ? words.substring(0, 50) + '...' : words;
}

function createTitleAndBulletsForm(content) {
    const title = content.title || '';
    const bullets = content.bullets || ['', '', '', '', ''];
    
    let bulletFields = '';
    for (let i = 0; i < 5; i++) {
        bulletFields += createFormField(`Bullet ${i+1}`, `bullet-${i}`, bullets[i] || '');
    }
    
    return `
        <h3>Edit Title and Bullets</h3>
        ${createFormField('Title', 'title', title)}
        <h4>Bullet Points</h4>
        ${bulletFields}
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
    `;
}

function createQuoteForm(content) {
    const quote = content.quote || '';
    const author = content.author || '';
    
    return `
        <h3>Edit Quote</h3>
        ${createTextAreaField('Quote', 'quote', quote)}
        ${createFormField('Author', 'author', author)}
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
    `;
}

function createImageAndParagraphForm(content) {
    const title = content.title || '';
    const paragraph = content.paragraph || '';
    const imageDescription = content.imageDescription || '';
    
    return `
        <h3>Edit Image and Paragraph</h3>
        ${createFormField('Title', 'title', title)}
        ${createFormField('Image Description', 'imageDescription', imageDescription)}
        ${createTextAreaField('Paragraph', 'paragraph', paragraph)}
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
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
        ${createFormField('Title', 'title', title)}
        <div class="form-row">
            <div class="col">
                <h4>Left Column</h4>
                ${createFormField('Column 1 Title', 'column1Title', column1Title)}
                ${createTextAreaField('Column 1 Content', 'column1Content', column1Content)}
            </div>
            <div class="col">
                <h4>Right Column</h4>
                ${createFormField('Column 2 Title', 'column2Title', column2Title)}
                ${createTextAreaField('Column 2 Content', 'column2Content', column2Content)}
            </div>
        </div>
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
    `;
}

function createTitleOnlyForm(content) {
    const title = content.title || '';
    const subtitle = content.subtitle || '';
    
    return `
        <h3>Edit Title Slide</h3>
        ${createFormField('Title', 'title', title)}
        ${createFormField('Subtitle', 'subtitle', subtitle)}
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
    `;
}

// New form creators for the new layouts

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
                ${createFormField('Feature Title', `feature-${i}-title`, feature.title || '')}
                ${createTextAreaField('Feature Description', `feature-${i}-description`, feature.description || '')}
            </div>
        `;
    }
    
    return `
        <h3>Edit Image with Features</h3>
        ${createFormField('Title', 'title', title)}
        ${createFormField('Image Description', 'imageDescription', imageDescription)}
        <h4>Features</h4>
        ${featuresFields}
        <button id="save-edit-btn" class="btn btn-primary">Save Changes</button>
    `;
}
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
    "sideBySideComparison"
]

function collectFormData(layout) {
    const formData = {};
    
    try {
        switch(layout) {
            case 'titleAndBullets':
                formData.title = document.getElementById('title')?.value || '';
                formData.bullets = [];
                for (let i = 0; i < 5; i++) {
                    const bulletElement = document.getElementById(`bullet-${i}`);
                    if (bulletElement && bulletElement.value && bulletElement.value.trim()) {
                        formData.bullets.push(bulletElement.value);
                    }
                }
                break;
                
            case 'quote':
                formData.quote = document.getElementById('quote')?.value || '';
                formData.author = document.getElementById('author')?.value || '';
                break;
                
            case 'imageAndParagraph':
                formData.title = document.getElementById('title')?.value || '';
                formData.imageDescription = document.getElementById('imageDescription')?.value || '';
                formData.paragraph = document.getElementById('paragraph')?.value || '';
                break;
                
            case 'twoColumn':
                formData.title = document.getElementById('title')?.value || '';
                formData.column1Title = document.getElementById('column1Title')?.value || '';
                formData.column1Content = document.getElementById('column1Content')?.value || '';
                formData.column2Title = document.getElementById('column2Title')?.value || '';
                formData.column2Content = document.getElementById('column2Content')?.value || '';
                break;
                
            case 'titleOnly':
                formData.title = document.getElementById('title')?.value || '';
                formData.subtitle = document.getElementById('subtitle')?.value || '';
                break;
                
            // New form data collectors
            case 'imageWithFeatures':
                formData.title = document.getElementById('title')?.value || '';
                formData.imageDescription = document.getElementById('imageDescription')?.value || '';
                formData.features = [];
                for (let i = 0; i < 4; i++) {
                    const titleElement = document.getElementById(`feature-${i}-title`);
                    const descriptionElement = document.getElementById(`feature-${i}-description`);
                    if (titleElement && descriptionElement && 
                        (titleElement.value.trim() || descriptionElement.value.trim())) {
                        formData.features.push({
                            title: titleElement.value,
                            description: descriptionElement.value
                        });
                    }
                }
                break;
                
            case 'numberedFeatures':
                formData.title = document.getElementById('title')?.value || '';
                formData.imageDescription = document.getElementById('imageDescription')?.value || '';
                formData.features = [];
                for (let i = 0; i < 4; i++) {
                    const titleElement = document.getElementById(`feature-${i}-title`);
                    const descriptionElement = document.getElementById(`feature-${i}-description`);
                    if (titleElement && descriptionElement && 
                        (titleElement.value.trim() || descriptionElement.value.trim())) {
                        formData.features.push({
                            number: i + 1,
                            title: titleElement.value,
                            description: descriptionElement.value
                        });
                    }
                }
                break; 
            case 'benefitsGrid':
                formData.title = document.getElementById('title')?.value || '';
                formData.imageDescription = document.getElementById('imageDescription')?.value || '';
                formData.benefits = [];
                for (let i = 0; i < 4; i++) {
                    const titleElement = document.getElementById(`benefit-${i}-title`);
                    const descriptionElement = document.getElementById(`benefit-${i}-description`);
                    if (titleElement && descriptionElement && 
                        (titleElement.value.trim() || descriptionElement.value.trim())) {
                        formData.benefits.push({
                            title: titleElement.value,
                            description: descriptionElement.value
                        });
                    }
                }
                break;
                
            case 'iconGrid':
                formData.title = document.getElementById('title')?.value || '';
                formData.categories = [];
                for (let i = 0; i < 8; i++) {
                    const nameElement = document.getElementById(`category-${i}-name`);
                    const descriptionElement = document.getElementById(`category-${i}-description`);
                    if (nameElement && descriptionElement && 
                        (nameElement.value.trim() || descriptionElement.value.trim())) {
                        formData.categories.push({
                            name: nameElement.value,
                            description: descriptionElement.value
                        });
                    }
                }
                break;
                
            case 'sideBySideComparison':
                formData.title = document.getElementById('title')?.value || '';
                formData.leftTitle = document.getElementById('leftTitle')?.value || '';
                formData.rightTitle = document.getElementById('rightTitle')?.value || '';
                
                formData.leftPoints = [];
                for (let i = 0; i < 3; i++) {
                    const pointElement = document.getElementById(`left-point-${i}`);
                    if (pointElement && pointElement.value && pointElement.value.trim()) {
                        formData.leftPoints.push(pointElement.value);
                    }
                }
                
                formData.rightPoints = [];
                for (let i = 0; i < 3; i++) {
                    const pointElement = document.getElementById(`right-point-${i}`);
                    if (pointElement && pointElement.value && pointElement.value.trim()) {
                        formData.rightPoints.push(pointElement.value);
                    }
                }
                break;
                
            case 'timeline':
                formData.title = document.getElementById('title')?.value || '';
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
                formData.title = document.getElementById('title')?.value || '';
                formData.summary = document.getElementById('summary')?.value || '';
                formData.nextSteps = [];
                for (let i = 0; i < 3; i++) {
                    const stepElement = document.getElementById(`next-step-${i}`);
                    if (stepElement && stepElement.value && stepElement.value.trim()) {
                        formData.nextSteps.push(stepElement.value);
                    }
                }
                break;
        }
    } catch (error) {
        console.error("Error in collectFormData:", error);
    }
    
    return formData;
}
if (!window.ppgLayouts) {
    window.ppgLayouts = {};
}

window.ppgLayouts.collectFormData = function(layout) {
    return collectFormData(layout);
};
function updateSaveButtonLabel() {
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.textContent = appState.presentationId ? 'Update' : 'Save';
        saveBtn.title = appState.presentationId 
            ? 'Update the existing presentation' 
            : 'Save as a new presentation';
    }
}
async function handleSave() {
    if (appState.editMode) {
        saveCurrentEdit();
    }

    if (!appState.slides || appState.slides.length === 0) {
        showNotification('No slides to save. Please generate a presentation first.', 'error');
        return;
    }

    document.getElementById('loading').classList.remove('hidden');

    // Enhanced save data with generation metadata
    const saveData = {
        topic: appState.topic,
        template: appState.templateId,
        slides: appState.slides,
        metadata: {
            generationMethod: appState.generationMethod || 'topic',
            contentStats: appState.contentStats || null,
            slideCount: appState.slides.length,
            lastModified: new Date().toISOString()
        }
    };

    const url = appState.presentationId 
        ? `/api/presentations/${appState.presentationId}/update`
        : '/api/save';

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(saveData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        const data = await response.json();

        if (!appState.presentationId) {
            appState.presentationId = data.presentation.id;
            window.history.pushState(
                {}, 
                '', 
                `/editor/${data.presentation.id}`
            );
            showNotification('Presentation created successfully!', 'success');
        } else {
            showNotification('Presentation updated successfully!', 'success');
        }

        appState.isModified = false;
        
    } catch (error) {
        console.error('Error saving presentation:', error);
        showNotification(error.message || 'Failed to save presentation', 'error');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

    async function handleExport() {
        if (!appState.slides || appState.slides.length === 0) {
            showNotification('Please generate slides first', 'error');
            return;
        }
        
        if (appState.editMode) {
            saveCurrentEdit();
        }
        
        loadingIndicator.classList.remove('hidden');
        exportBtn.disabled = true;
        
        try {
            const response = await fetch('/api/export-local', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    slides: appState.slides,
                    template: appState.templateId,
                    topic: appState.topic
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${appState.topic.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_presentation.pptx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            
            showNotification('Presentation exported successfully!', 'success');
        } catch (error) {
            console.error('Error exporting to PPTX:', error);
            showNotification('Failed to export presentation. Please try again.', 'error');
        } finally {
            loadingIndicator.classList.add('hidden');
            exportBtn.disabled = false;
        }
    }
    
function handleRegenerate() {
    if (appState.editMode) {
        exitEditMode();
    }
    if (appState.presentationId && confirm('Regenerating will create a new presentation. Save changes to the current presentation first?')) {
        handleSave(); // Save current presentation before regenerating
    }
    appState.presentationId = null; // Reset to indicate a new presentation
    handleGenerate();
}
    
function renderSlidesList() {
    const slidesList = document.getElementById('slides-list');
    
    if (!appState.slides || appState.slides.length === 0) {
        slidesList.innerHTML = `
            <div class="slides-placeholder">
                Slides will appear here after generation
            </div>
        `;
        return;
    }
    
    let slidesHtml = '';
    
    appState.slides.forEach((slide, index) => {
        const isActive = index === appState.currentSlideIndex;
        
        slidesHtml += `
            <div class="slide-thumbnail ${isActive ? 'active' : ''}" data-index="${index}">
                <div class="slide-thumbnail-content">
                    ${window.ppgLayouts.renderPreview(slide.layout, slide.content, appState.templateId)}
                </div>
                <div class="slide-actions">
                    <span class="slide-number">Slide ${index + 1}</span>
                    <button class="btn-icon delete-slide" data-index="${index}"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
    });
    
    slidesList.innerHTML = slidesHtml;
    
    // Add click events to thumbnails
    const thumbnails = slidesList.querySelectorAll('.slide-thumbnail');
    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', () => {
            const index = parseInt(thumbnail.dataset.index);
            if (appState.currentSlideIndex !== index) {
                // Check for unsaved changes if in edit mode
                if (appState.editMode && typeof appState.editMode !== 'string') {
                    const confirmChange = confirm('You have unsaved changes. Continue without saving?');
                    if (!confirmChange) return;
                    cancelEdit();
                }
                
                appState.currentSlideIndex = index;
                renderCurrentSlide();
                renderSlidesList(); // Re-render to update active state
            }
        });
    });
    
    // Add click events to delete buttons
    const deleteButtons = slidesList.querySelectorAll('.delete-slide');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent thumbnail click
            const index = parseInt(button.dataset.index);
            deleteSlide(index);
        });
    });
    
    // Enable drag and drop for reordering
    enableDragAndDrop();
}

function deleteSlide(index) {
    if (appState.slides.length <= 1) {
        alert('Cannot delete the only slide. Presentations must have at least one slide.');
        return;
    }
    
    const confirmDelete = confirm('Are you sure you want to delete this slide?');
    if (!confirmDelete) return;
    
    appState.slides.splice(index, 1);
    
    if (appState.currentSlideIndex >= appState.slides.length) {
        appState.currentSlideIndex = appState.slides.length - 1;
    } else if (appState.currentSlideIndex === index) {
        appState.currentSlideIndex = Math.min(appState.currentSlideIndex, appState.slides.length - 1);
    }
    
    appState.isModified = true;
    
    renderSlidesList();
    renderCurrentSlide();
    
    showNotification('Slide deleted', 'success');
}
    function renderCurrentSlide() {
        const slideData = appState.slides[appState.currentSlideIndex];
        const slidePreview = document.getElementById('slide-preview');
        
        if (!slideData) {
            slidePreview.innerHTML = `
                <div class="placeholder-message">
                    No slide data available
                </div>
            `;
            return;
        }
        
        if (appState.editMode && document.getElementById('edit-form').classList.contains('hidden') === false) {
            return;
        }
        
        const template = getTemplateById(appState.templateId);
        
        const slideHtml = window.ppgLayouts.renderPreview(slideData.layout, slideData.content, appState.templateId);
        
        slidePreview.innerHTML = slideHtml;
        
        renderSlideControls();
        
        updateEditControls();
    }
    function renderSlideControls() {
        if (appState.slides.length <= 1) {
            slidesControls.innerHTML = '';
            return;
        }
        
        const controlsHtml = `
            <span class="slide-indicator">
                Slide ${appState.currentSlideIndex + 1} of ${appState.slides.length}
            </span>
            <div class="slide-navigation">
                <button id="prev-slide" class="btn" ${appState.currentSlideIndex === 0 ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                <button id="next-slide" class="btn" ${appState.currentSlideIndex === appState.slides.length - 1 ? 'disabled' : ''}>
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        slidesControls.innerHTML = controlsHtml;
        
        // Add event listeners
        const prevBtn = document.getElementById('prev-slide');
        const nextBtn = document.getElementById('next-slide');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', showPreviousSlide);
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', showNextSlide);
        }
    }
    

    function enterEditMode() {
        appState.editMode = true;
        renderCurrentSlide();
    }
    
    // Exit edit mode without saving
    function exitEditMode() {
        appState.editMode = false;
        renderCurrentSlide();
    }
    

    function escapeHTML(str) {
        if (!str || typeof str !== 'string') return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function removeBulletPoint(e) {
        const container = document.getElementById('bullet-points-container');
        const bulletInput = e.target.parentElement;
        container.removeChild(bulletInput);
        
        // Renumber the remaining bullet points
        const bulletInputs = container.querySelectorAll('.bullet-point-input');
        bulletInputs.forEach((input, index) => {
            const inputField = input.querySelector('input');
            inputField.name = `bullet-${index}`;
            const removeBtn = input.querySelector('.remove-bullet');
            removeBtn.dataset.index = index;
        });
    }
    
    // Show previous slide
    function showPreviousSlide() {
        if (appState.currentSlideIndex > 0) {
            if (appState.editMode) {
                const confirmChange = confirm('You have unsaved changes. Do you want to continue?');
                if (confirmChange) {
                    appState.editMode = false;
                    appState.currentSlideIndex--;
                    renderCurrentSlide();
                    renderSlidesList();
                }
            } else {
                appState.currentSlideIndex--;
                renderCurrentSlide();
                renderSlidesList();
            }
        }
    }
    
    // Show next slide
    function showNextSlide() {
        if (appState.currentSlideIndex < appState.slides.length - 1) {
            if (appState.editMode) {
                const confirmChange = confirm('You have unsaved changes. Do you want to continue?');
                if (confirmChange) {
                    appState.editMode = false;
                    appState.currentSlideIndex++;
                    renderCurrentSlide();
                    renderSlidesList();
                }
            } else {
                appState.currentSlideIndex++;
                renderCurrentSlide();
                renderSlidesList();
            }
        }
    }
    
    // Handle keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (appState.slides.length <= 1 || appState.editMode) return;
        
        // Left arrow key
        if (e.key === 'ArrowLeft' && appState.currentSlideIndex > 0) {
            showPreviousSlide();
        }
        // Right arrow key
        else if (e.key === 'ArrowRight' && appState.currentSlideIndex < appState.slides.length - 1) {
            showNextSlide();
        }
    });
    // Add this function to editor.js
function enableDragAndDrop() {
    const slidesList = document.getElementById('slides-list');
    if (!slidesList) return;
    
    const slideThumbnails = slidesList.querySelectorAll('.slide-thumbnail');
    if (!slideThumbnails.length) return;
    
    slideThumbnails.forEach(item => {
        // Skip if already set up
        if (item.getAttribute('data-drag-initialized') === 'true') return;
        
        item.setAttribute('draggable', 'true');
        item.setAttribute('data-drag-initialized', 'true');
        
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', item.dataset.index);
            item.classList.add('dragging');
        });
        
        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
        });
        
        item.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        item.addEventListener('drop', (e) => {
            e.preventDefault();
            const fromIndex = parseInt(e.dataTransfer.getData('text/plain'));
            const toIndex = parseInt(item.dataset.index);
            
            if (fromIndex !== toIndex) {
                // Reorder slides
                const [movedSlide] = appState.slides.splice(fromIndex, 1);
                appState.slides.splice(toIndex, 0, movedSlide);
                
                // Adjust current index if needed
                if (appState.currentSlideIndex === fromIndex) {
                    appState.currentSlideIndex = toIndex;
                } else if (appState.currentSlideIndex > fromIndex && appState.currentSlideIndex <= toIndex) {
                    appState.currentSlideIndex--;
                } else if (appState.currentSlideIndex < fromIndex && appState.currentSlideIndex >= toIndex) {
                    appState.currentSlideIndex++;
                }
                
                // Mark as modified
                appState.isModified = true;
                
                // Re-render
                renderSlidesList();
                renderCurrentSlide();
            }
        });
    });
}
    // Show notification
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
    
    // Show notification
    notification.classList.add('show');
    
    // Auto-hide after duration
    setTimeout(() => {
        notification.classList.remove('show');
    }, duration);
    
    // For errors, keep them visible longer
    if (type === 'error') {
        setTimeout(() => {
            notification.classList.remove('show');
        }, duration * 1.5);
    }
}
    
    // Check for unsaved changes before leaving
    window.addEventListener('beforeunload', (e) => {
        if (appState.isModified) {
            const message = 'You have unsaved changes. Are you sure you want to leave?';
            e.returnValue = message;
            return message;
        }
    });
    
    // Initialize with placeholder message
    if (slidePreview.innerHTML.trim() === '') {
        slidePreview.innerHTML = `
            <div class="placeholder-message">
                Your slide preview will appear here after generating content
            </div>
        `;
    }
    function getLayoutById(layoutId) {
        return layouts.find(layout => layout.id === layoutId) || null;
    }


function renderEditorContent(appState) {
    switch(appState.editMode) {
        case 'content':
            return renderContentEditor(appState);
        case 'layout':
            return renderLayoutSelector(appState);
        case 'manage':
            return renderSlideManager(appState);
        default:
            return renderContentEditor(appState);
    }
}

function renderContentEditor(appState) {
    const currentSlide = appState.slides[appState.currentSlideIndex];
    return window.ppgLayouts.createEditForm(currentSlide.layout, currentSlide.content);
}

function renderLayoutSelector(appState) {
    const currentLayout = appState.slides[appState.currentSlideIndex].layout;
    
    let layoutOptionsHtml = '';
    window.ppgLayouts.layouts.forEach(layout => {
        layoutOptionsHtml += `
            <div class="layout-option ${layout.id === currentLayout ? 'selected' : ''}" 
                 onclick="changeSlideLayout('${layout.id}')">
                <div class="layout-icon"><i class="fas ${layout.icon}"></i></div>
                <div class="layout-info">
                    <h4>${layout.name}</h4>
                    <p>${layout.description}</p>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="layout-selector">
            <h3>Choose a Layout</h3>
            <p class="note">Changing layout will reset slide content. Make sure to save any important content first.</p>
            <div class="layout-options">
                ${layoutOptionsHtml}
            </div>
        </div>
    `;
}

// Interface for managing slides (add, delete, reorder)
function renderSlideManager(appState) {
    let slidesListHtml = '';
    
    appState.slides.forEach((slide, index) => {
        slidesListHtml += `
            <div class="slide-item ${index === appState.currentSlideIndex ? 'active' : ''}" 
                 data-index="${index}" draggable="true" ondragstart="dragStart(event)" ondrop="drop(event)" 
                 ondragover="allowDrop(event)" onclick="selectSlide(${index})">
                <div class="slide-thumbnail">
                    ${window.ppgLayouts.renderPreview(slide.layout, slide.content, appState.templateId)}
                </div>
                <div class="slide-actions">
                    <button class="btn-icon" onclick="deleteSlide(${index})"><i class="fas fa-trash"></i></button>
                    <span class="slide-number">Slide ${index + 1}</span>
                </div>
            </div>
        `;
    });
    
    return `
        <div class="slide-manager">
            <h3>Manage Slides</h3>
            <p>Drag slides to reorder, click to select, or use buttons to add/delete slides.</p>
            
            <div class="manager-actions">
                <button class="btn btn-secondary" onclick="addNewSlide()">Add New Slide</button>
            </div>
            
            <div class="slides-list">
                ${slidesListHtml}
            </div>
        </div>
    `;
}


// Switch between edit modes
// function switchEditMode(mode) {
//     appState.editMode = mode;
//     renderCurrentSlide();
// }

function changeSlideLayout() {
    const currentSlide = window.appState.slides[window.appState.currentSlideIndex];
    if (!currentSlide) return;
    
    // Create modal overlay for blur effect
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'change-layout-modal-overlay';
    modalOverlay.className = 'modal-overlay';
    document.body.appendChild(modalOverlay);
    
    // Create modal content container
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalOverlay.appendChild(modalContent);
    
    // Add close button
    // const closeButton = document.createElement('span');
    // closeButton.className = 'modal-close';
    // closeButton.innerHTML = '&times;';
    // closeButton.addEventListener('click', function() {
    //     document.body.removeChild(modalOverlay);
    //     window.appState.editMode = false;
    // });
    // modalContent.appendChild(closeButton);
    
    // Create layout selector HTML
    const layouts = window.ppgLayouts.layouts;
    
    let layoutOptionsHtml = '<div class="layout-options">';
    layouts.forEach(layout => {
        layoutOptionsHtml += `
            <div class="layout-option ${layout.id === currentSlide.layout ? 'selected' : ''}" 
                 data-layout="${layout.id}">
                <div class="layout-icon"><i class="fas ${layout.icon}"></i></div>
                <div class="layout-info">
                    <h4>${layout.name}</h4>
                    <p>${layout.description}</p>
                </div>
            </div>
        `;
    });
    layoutOptionsHtml += '</div>';
    
    const formHtml = `
        <div class="layout-selector">
            <h2>Change Slide Layout</h2>
            <p class="warning">Changing layout will reset the slide content. Save any important content first.</p>
            
            ${layoutOptionsHtml}
            
            <div class="layout-selector-actions">
                <button id="change-layout-btn" class="btn btn-primary">Change Layout</button>
                <button id="cancel-layout-btn" class="btn btn-secondary">Cancel</button>
            </div>
        </div>
    `;
    
    // Add the form HTML to the modal
    modalContent.innerHTML += formHtml;
    
    // Add event listeners
    modalContent.querySelector('#change-layout-btn').addEventListener('click', function() {
        const selectedLayout = modalOverlay.querySelector('.layout-option.selected');
        if (!selectedLayout) {
            alert('Please select a layout');
            return;
        }
        
        const newLayout = selectedLayout.dataset.layout;
        
        // Only proceed if the layout is actually changing
        if (newLayout === currentSlide.layout) {
            document.body.removeChild(modalOverlay);
            window.appState.editMode = false;
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
        window.appState.isModified = true;
        
        // Close the modal
        document.body.removeChild(modalOverlay);
        
        // Exit edit mode
        window.appState.editMode = false;
        
        // Re-render
        renderCurrentSlide();
        renderSlidesList();
        
        showNotification('Slide layout changed successfully!', 'success');
    });
    
    modalContent.querySelector('#cancel-layout-btn').addEventListener('click', function() {
        document.body.removeChild(modalOverlay);
        window.appState.editMode = false;
    });
    
    // Add click events to layout options
    const layoutOptions = modalContent.querySelectorAll('.layout-option');
    layoutOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Deselect all options
            layoutOptions.forEach(opt => opt.classList.remove('selected'));
            // Select the clicked option
            option.classList.add('selected');
        });
    });
    
    // Set edit mode
    window.appState.editMode = 'layout-change';
}

function updateEditControls() {
    const editControlsContainer = document.getElementById('external-edit-controls');
    
    if (!window.appState.slides || window.appState.slides.length === 0 || window.appState.editMode) {
        editControlsContainer.classList.add('hidden');
        return;
    }
    
    editControlsContainer.classList.remove('hidden');
    
    editControlsContainer.innerHTML = `
        <div class="edit-buttons">
            <button id="edit-content-btn" class="btn btn-primary"><i class="fas fa-edit"></i> Edit Content</button>
            <button id="change-layout-btn" class="btn btn-secondary"><i class="fas fa-th-large"></i> Change Layout</button>
        </div>
        <div class="slide-actions">
            <button id="add-slide-btn" class="btn btn-secondary"><i class="fas fa-plus"></i> Add Slide</button>
            <button id="delete-slide-btn" class="btn btn-danger"><i class="fas fa-trash"></i> Delete Slide</button>
        </div>
    `;
    
    // Add event listeners
    document.getElementById('edit-content-btn').addEventListener('click', showEditForm);
    document.getElementById('change-layout-btn').addEventListener('click', changeSlideLayout);
    document.getElementById('add-slide-btn').addEventListener('click', addNewSlide);
    document.getElementById('delete-slide-btn').addEventListener('click', deleteCurrentSlide);
}


// Add to editor.js
function addNewSlide() {
    showLayoutSelector();
}

function addSlideWithSelectedLayout(modalOverlay) {
    const selectedLayout = modalOverlay.querySelector('.layout-option.selected');
    if (!selectedLayout) {
        alert('Please select a layout');
        return;
    }
    
    const layout = selectedLayout.dataset.layout;
    const content = generateDefaultContent(layout);
    
    // Add to slides array with isUserCreated flag
    window.appState.slides.push({
        layout,
        content,
        isUserCreated: true // This flag indicates user-created slides
    });
    
    // Switch to the new slide
    window.appState.currentSlideIndex = window.appState.slides.length - 1;
    
    // Mark as modified
    window.appState.isModified = true;
    
    // Remove the modal
    document.body.removeChild(modalOverlay);
    
    // Exit layout selection mode
    window.appState.editMode = false;
    
    // Render the new slide
    renderSlidesList();
    renderCurrentSlide();
    
    showNotification('New slide added', 'success');
}

function showEditForm() {
    const currentSlide = window.appState.slides[window.appState.currentSlideIndex];
    if (!currentSlide) return;
    
    // Create modal overlay for blur effect
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'edit-modal-overlay';
    modalOverlay.className = 'modal-overlay';
    document.body.appendChild(modalOverlay);
    
    // Create modal content container
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalOverlay.appendChild(modalContent);
    
    const formHtml = window.ppgLayouts.createEditForm(currentSlide.layout, currentSlide.content);
    modalContent.innerHTML += formHtml;
    
    // Add event listeners to form buttons
    const saveBtn = modalContent.querySelector('#save-edit-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveCurrentEdit(currentSlide, modalOverlay);
        });
    }
    
    const cancelBtn = modalContent.querySelector('#cancel-edit-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            document.body.removeChild(modalOverlay);
            window.appState.editMode = false;
        });
    }
    
    // Set edit mode
    window.appState.editMode = 'content-edit';
}

function cancelEdit() {
    const editForm = document.getElementById('edit-form');
    const slidePreview = document.getElementById('slide-preview');
    
    // Hide the form and show the preview
    editForm.classList.add('hidden');
    slidePreview.classList.remove('hidden');
    
    // Exit edit mode
    window.appState.editMode = false;
}

function saveCurrentEdit(slide, modalOverlay) {
    const layout = slide.layout;
    
    // Collect form data based on the layout type
    const formData = window.ppgLayouts.collectFormData(layout);
    
    // Update the slide content
    slide.content = formData;
    
    // Mark as modified
    window.appState.isModified = true;
    
    // Remove the modal
    if (modalOverlay && modalOverlay.parentNode) {
        document.body.removeChild(modalOverlay);
    }
    
    // Exit edit mode
    window.appState.editMode = false;
    
    // Re-render the slide
    renderCurrentSlide();
    renderSlidesList();
    
    showNotification('Slide updated successfully!', 'success');
}


function showLayoutSelector() {
    // Create modal overlay for blur effect
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'layout-modal-overlay';
    modalOverlay.className = 'modal-overlay';
    document.body.appendChild(modalOverlay);
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalOverlay.appendChild(modalContent);
    
    const layouts = window.ppgLayouts.layouts;
    
    let layoutOptionsHtml = '<div class="layout-options">';
    layouts.forEach(layout => {
        layoutOptionsHtml += `
            <div class="layout-option" data-layout="${layout.id}">
                <div class="layout-icon"><i class="fas ${layout.icon}"></i></div>
                <div class="layout-info">
                    <h4>${layout.name}</h4>
                    <p>${layout.description}</p>
                </div>
            </div>
        `;
    });
    layoutOptionsHtml += '</div>';
    
    const formHtml = `
        <div class="layout-selector">
            <h2>Select Layout for New Slide</h2>
            <p>Choose a layout for your new slide:</p>
            
            ${layoutOptionsHtml}
            
            <div class="layout-selector-actions">
                <button id="add-slide-with-layout-btn" class="btn btn-primary">Add Slide</button>
                <button id="cancel-add-slide-btn" class="btn btn-secondary">Cancel</button>
            </div>
        </div>
    `;
    
    // Add the form HTML to the modal
    modalContent.innerHTML += formHtml;
    
    // Add event listeners
    modalContent.querySelector('#add-slide-with-layout-btn').addEventListener('click', function() {
        addSlideWithSelectedLayout(modalOverlay);
    });
    
    modalContent.querySelector('#cancel-add-slide-btn').addEventListener('click', function() {
        document.body.removeChild(modalOverlay);
        window.appState.editMode = false;
    });
    
    // Add click events to layout options
    const layoutOptions = modalContent.querySelectorAll('.layout-option');
    layoutOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Deselect all options
            layoutOptions.forEach(opt => opt.classList.remove('selected'));
            // Select the clicked option
            option.classList.add('selected');
        });
    });
    
    // Select the first layout by default
    if (layoutOptions.length > 0) {
        layoutOptions[0].classList.add('selected');
    }
    
    // Set edit mode
    window.appState.editMode = 'layout-selection';
}





function generateDefaultContent(layout) {
    const topic = window.appState.topic || 'Presentation';
    
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
case 'conclusion':
            return {
                title: `Key Takeaways from ${topic}`,
                summary: `A comprehensive overview of the main points covered in this presentation about ${topic}.`,
                nextSteps: [
                    `Implement the insights from ${topic}`,
                    "Schedule a follow-up discussion",
                    "Share this presentation with stakeholders"
                ]
            };
        
        default:     
            return {};
    }
}
// Add to editor.js
function deleteCurrentSlide() {
    if (appState.slides.length <= 1) {
        alert('Cannot delete the only slide. Presentations must have at least one slide.');
        return;
    }
    
    const confirmDelete = confirm('Are you sure you want to delete this slide?');
    if (!confirmDelete) return;
    
    // Remove the slide
    appState.slides.splice(appState.currentSlideIndex, 1);
    
    // Adjust current index if needed
    if (appState.currentSlideIndex >= appState.slides.length) {
        appState.currentSlideIndex = appState.slides.length - 1;
    }
    
    // Mark as modified
    appState.isModified = true;
    
    // Re-render
    renderSlidesList();
    renderCurrentSlide();
    
    showNotification('Slide deleted', 'success');
}

function updateEditControls() {
    const editControlsContainer = document.getElementById('external-edit-controls');
    
    if (!window.appState.slides || window.appState.slides.length === 0 || window.appState.editMode) {
        editControlsContainer.classList.add('hidden');
        return;
    }
    
    editControlsContainer.classList.remove('hidden');
    
    editControlsContainer.innerHTML = `
        <div class="edit-buttons">
            <button id="edit-content-btn" class="btn btn-primary"><i class="fas fa-edit"></i> Edit Content</button>
        </div>
        <div class="slide-actions">
            <button id="add-slide-btn" class="btn btn-secondary"><i class="fas fa-plus"></i> Add Slide</button>
            <button id="delete-slide-btn" class="btn btn-danger"><i class="fas fa-trash"></i> Delete Slide</button>
        </div>
    `;
    
    // Add event listeners
    document.getElementById('edit-content-btn').addEventListener('click', showEditForm);
    document.getElementById('add-slide-btn').addEventListener('click', addNewSlide);
    document.getElementById('delete-slide-btn').addEventListener('click', deleteCurrentSlide);
}
function initializeEditButtons() {
    // Add click handler for the Edit Content button
    const editContentBtn = document.getElementById('edit-content-btn');
    if (editContentBtn) {
        editContentBtn.addEventListener('click', showEditForm);
    }
    
    // Add click handler for the Change Layout button
    const changeLayoutBtn = document.getElementById('change-layout-btn');
    if (changeLayoutBtn) {
        changeLayoutBtn.addEventListener('click', changeSlideLayout);
    }
    
    // Add click handler for the Add New Slide button
    const addSlideBtn = document.getElementById('add-slide-btn');
    if (addSlideBtn) {
        addSlideBtn.addEventListener('click', addNewSlide);
    }
    
    // Add click handler for the Delete Slide button
    const deleteSlideBtn = document.getElementById('delete-slide-btn');
    if (deleteSlideBtn) {
        deleteSlideBtn.addEventListener('click', deleteCurrentSlide);
    }
    
    // Add click handler for export button
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', handleExport);
    }
    
    // Add click handler for save button
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', handleSave);
    }
    
    // Add click handler for previous slide button
    const prevSlideBtn = document.getElementById('prev-slide');
    if (prevSlideBtn) {
        prevSlideBtn.addEventListener('click', showPreviousSlide);
    }
    
    // Add click handler for next slide button
    const nextSlideBtn = document.getElementById('next-slide');
    if (nextSlideBtn) {
        nextSlideBtn.addEventListener('click', showNextSlide);
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (window.appState.slides.length <= 1 || window.appState.editMode) return;
        
        // Left arrow key
        if (e.key === 'ArrowLeft' && window.appState.currentSlideIndex > 0) {
            showPreviousSlide();
        }
        // Right arrow key
        else if (e.key === 'ArrowRight' && window.appState.currentSlideIndex < window.appState.slides.length - 1) {
            showNextSlide();
        }
    });}
});


