// FIXED INITIALIZATION ORDER - Replace your DOMContentLoaded with this:

document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Editor initializing...');

    // STEP 1: Initialize appState FIRST (before anything else)
    window.appState = {
        slides: [],
        templateId: null,
        topic: null,
        currentSlideIndex: 0,
        editMode: false,
        presentationId: null,
        isModified: false,
        isGenerating: false
    };
    console.log('✅ AppState initialized');

    // STEP 2: Get DOM elements
    const templatesContainer = document.getElementById('templates-container');
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

    console.log('📋 DOM Elements check:', {
        templatesContainer: !!templatesContainer,
        slidesList: !!slidesList,
        slidePreview: !!slidePreview,
        exportBtn: !!exportBtn,
        saveBtn: !!saveBtn,
        generateBtn: !!generateBtn
    });

    // STEP 3: Check for generated presentation IMMEDIATELY after appState init
    const urlParams = new URLSearchParams(window.location.search);
    const isGenerated = urlParams.get('generated') === 'true';

    if (isGenerated) {
        console.log('🎯 Loading generated presentation...');
        loadGeneratedPresentation();
    } else if (window.existingPresentation) {
        console.log('📂 Loading existing presentation...');
        initializeWithExistingPresentation(window.existingPresentation);
    }

    // STEP 4: Initialize other components
    if (templatesContainer) {
        initializeTemplateSelector();
    }

    if (!window.inputMethodsHandler && (topicInput || methodTabs.length > 0)) {
        window.inputMethodsHandler = new InputMethodsHandler();
    }

    // STEP 5: Add event listeners (with null checks)
    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerate);
    }
    if (exportBtn) {
        exportBtn.addEventListener('click', handleExport);
    }
    if (saveBtn) {
        saveBtn.addEventListener('click', handleSave);
    }
    if (editSlideBtn) {
        editSlideBtn.addEventListener('click', showEditForm);
    }

    // Method tabs
    methodTabs.forEach(tab => {
        tab.addEventListener('click', function () {
            const method = this.dataset.method;
            const event = new CustomEvent('input-method-changed', {
                detail: { method: method }
            });
            document.dispatchEvent(event);
        });
    });

    // Input method changed event
    document.addEventListener('input-method-changed', function (e) {
        const method = e.detail.method;
        const buttonTexts = {
            topic: '<i class="fas fa-magic"></i> Generate Presentation',
            text: '<i class="fas fa-file-text"></i> Generate from Text (AI Auto-Count)',
            document: '<i class="fas fa-file-upload"></i> Generate from Document (AI Auto-Count)'
        };

        if (generateBtn) {
            generateBtn.innerHTML = buttonTexts[method] || buttonTexts.topic;
        }
    });

    // Beforeunload handler
    window.addEventListener('beforeunload', function (e) {
        if (window.appState.isGenerating) {
            e.preventDefault();
            e.returnValue = 'Presentation is currently being generated. Are you sure you want to leave?';
            return e.returnValue;
        }
    });

    console.log('🎉 Editor initialization complete');


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


    function loadGeneratedPresentation() {
        try {
            const storedData = sessionStorage.getItem('generatedPresentation');

            if (!storedData) {
                console.error('❌ No generated presentation data found');
                showNotification('No presentation data found. Please generate again.', 'error');
                return;
            }

            const generatedData = JSON.parse(storedData);
            console.log('📱 Loading generated data:', generatedData);

            // Validate the data
            if (!generatedData.slides || !Array.isArray(generatedData.slides) || generatedData.slides.length === 0) {
                console.error('❌ Invalid slides data:', generatedData.slides);
                showNotification('Invalid presentation data. Please generate again.', 'error');
                return;
            }

            // Update application state
            window.appState.slides = generatedData.slides;
            window.appState.templateId = generatedData.template || 'corporate';
            window.appState.topic = generatedData.topic || 'Generated Presentation';
            window.appState.currentSlideIndex = 0;
            window.appState.editMode = false;
            window.appState.presentationId = null; // New presentation
            window.appState.isModified = true;
            window.appState.generationMethod = generatedData.generationMethod || 'generated';
            window.appState.outline = generatedData.outline;

            // Set the selected template
            window.selectedTemplateId = generatedData.template || 'corporate';

            // Update form fields
            const topicInput = document.getElementById('topic');
            if (topicInput) {
                topicInput.value = window.appState.topic;
            }

            const slideCountInput = document.getElementById('slide-count');
            if (slideCountInput) {
                slideCountInput.value = window.appState.slides.length;
            }

            // Set template selection in UI
            setTimeout(() => {
                document.querySelectorAll('.template-card').forEach(card => {
                    card.classList.remove('selected');
                    if (card.dataset.id === window.appState.templateId) {
                        card.classList.add('selected');
                    }
                });
            }, 100);

            // Enable buttons
            const exportBtn = document.getElementById('export-btn');
            const saveBtn = document.getElementById('save-btn');

            if (exportBtn) exportBtn.disabled = false;
            if (saveBtn) saveBtn.disabled = false;

            // Render the slides
            renderSlidesList();
            renderCurrentSlide();
            updateSaveButtonLabel();

            // Clear the stored data
            sessionStorage.removeItem('generatedPresentation');

            // Show success message
            showNotification(
                `✅ Presentation loaded successfully! ${generatedData.slides.length} slides generated.`,
                'success',
                5000
            );

            console.log('✅ Generated presentation loaded successfully');

        } catch (error) {
            console.error('❌ Error loading generated presentation:', error);
            showNotification('Error loading presentation data. Please generate again.', 'error');
        }
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
        const inputMethod = window.inputMethodsHandler.getCurrentMethod();

        console.log('Starting generation with method:', inputMethod);

        // Check if user wants outline for this method
        const useOutline = shouldUseOutline(inputMethod);

        if (useOutline) {
            await handleGenerationWithOutline(inputMethod);
            return;
        }

        // Direct generation without outline
        await handleDirectGeneration(inputMethod);
    }
    // 2. NEW: Determine if outline should be used
    function shouldUseOutline(inputMethod) {
        // Check user preference or default settings
        const outlinePreferences = {
            'topic': true,        // Always use outline for topics
            'text': getUserPreference('text_outline', true),     // Default: true
            'document': getUserPreference('document_outline', true)  // Default: true
        };

        return outlinePreferences[inputMethod] || false;
    }

    // 3. NEW: Get user preference (can be stored in localStorage)
    function getUserPreference(key, defaultValue) {
        try {
            const stored = localStorage.getItem(`outline_pref_${key}`);
            return stored !== null ? JSON.parse(stored) : defaultValue;
        } catch (error) {
            return defaultValue;
        }
    }

    // 4. NEW: Set user preference
    function setUserPreference(key, value) {
        try {
            localStorage.setItem(`outline_pref_${key}`, JSON.stringify(value));
        } catch (error) {
            console.warn('Could not save user preference:', error);
        }
    }

    // 5. NEW: Handle generation with outline for any input method
    async function handleGenerationWithOutline(inputMethod) {
        try {
            let contentData = null;
            let topic = '';
            let slideCount = 5;

            // Prepare data based on input method
            switch (inputMethod) {
                case 'topic':
                    topic = document.getElementById('topic').value.trim();
                    slideCount = parseInt(document.getElementById('slide-count').value, 10) || 5;

                    if (!topic) {
                        showNotification('Please enter a presentation topic', 'error');
                        return;
                    }
                    break;

                case 'text':
                    const textContent = window.inputMethodsHandler.getTextContent();
                    if (!textContent || textContent.length < 50) {
                        showNotification('Please provide at least 50 characters of text content', 'error');
                        return;
                    }

                    // Process text content
                    const textResult = await window.inputMethodsHandler.processTextContent();
                    contentData = textResult.content;
                    topic = document.getElementById('topic').value.trim() || extractTopicFromContent(contentData) || 'Text Presentation';
                    slideCount = estimateSlideCount(textContent);
                    break;

                case 'document':
                    const processedContent = window.inputMethodsHandler.getProcessedContent();
                    if (!processedContent) {
                        showNotification('Please upload and process a document first', 'error');
                        return;
                    }

                    contentData = processedContent;
                    topic = document.getElementById('topic').value.trim() || extractTopicFromContent(contentData) || 'Document Presentation';
                    slideCount = estimateSlideCount(contentData.full_text);
                    break;
            }

            if (!window.selectedTemplateId) {
                showNotification('Please select a template', 'error');
                return;
            }

            // Show outline generation modal
            await showOutlineGenerationModal(topic, slideCount, inputMethod, contentData);

        } catch (error) {
            console.error('Error in outline generation:', error);
            showNotification('Failed to start outline generation. Please try again.', 'error');
        }
    }

    // 2. NEW: Handle topic generation with outline modal
    async function handleTopicGenerationWithOutline() {
        const topicInput = document.getElementById('topic');
        const slideCountInput = document.getElementById('slide-count');

        const topic = topicInput.value.trim();
        const slideCount = parseInt(slideCountInput.value, 10) || 5;

        if (!topic) {
            showNotification('Please enter a presentation topic', 'error');
            return;
        }

        if (!window.selectedTemplateId) {
            showNotification('Please select a template', 'error');
            return;
        }

        if (isNaN(slideCount) || slideCount < 1 || slideCount > 10) {
            showNotification('Please enter a valid slide count (1-10)', 'error');
            return;
        }

        try {
            // Step 1: Generate outline
            await showOutlineGenerationModal(topic, slideCount);

        } catch (error) {
            console.error('Error in topic generation with outline:', error);
            showNotification('Failed to generate outline. Please try again.', 'error');
        }
    }

    async function showOutlineGenerationModal(topic, slideCount, inputMethod, contentData = null) {
        // Create modal overlay
        const modalOverlay = document.createElement('div');
        modalOverlay.id = 'outline-generation-modal';
        modalOverlay.className = 'modal-overlay';
        document.body.appendChild(modalOverlay);

        // Create modal content
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content outline-modal';
        modalOverlay.appendChild(modalContent);

        // Show loading state with method-specific message
        const loadingMessages = {
            'topic': 'Analyzing your topic and creating the perfect presentation structure...',
            'text': 'Analyzing your text content and organizing it into a coherent presentation flow...',
            'document': 'Processing your document and extracting key insights for a structured presentation...'
        };

        modalContent.innerHTML = `
        <div class="outline-modal-header">
            <h2><i class="fas fa-robot"></i> AI Presentation Planner</h2>
            <button class="modal-close" onclick="closeOutlineModal()">&times;</button>
        </div>
        <div class="outline-modal-body">
            <div class="outline-loading">
                <div class="loading-spinner"></div>
                <h3>Creating your presentation outline...</h3>
                <p>${loadingMessages[inputMethod]}</p>
                <div class="loading-details">
                    <div class="detail-item">
                        <span class="detail-label">Input Method</span>
                        <span class="detail-value">${getInputMethodDisplayName(inputMethod)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Topic</span>
                        <span class="detail-value">${topic}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Estimated Slides</span>
                        <span class="detail-value">${slideCount}</span>
                    </div>
                    ${contentData ? `
                    <div class="detail-item">
                        <span class="detail-label">Content Length</span>
                        <span class="detail-value">${formatContentLength(contentData)}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

        try {
            // Generate outline based on input method
            const outline = await generateOutlineFromInput(topic, slideCount, inputMethod, contentData);

            // Show outline for approval
            showOutlineForApproval(modalContent, outline, topic, slideCount, inputMethod, contentData);

        } catch (error) {
            console.error('Error generating outline:', error);
            showOutlineError(modalContent, error.message, inputMethod, contentData);
        }
    }


    // 4. NEW: Generate outline for topic
    async function generateOutlineForTopic(topic, slideCount) {
        const response = await fetch('/api/generate-outline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                topic: topic,
                slideCount: slideCount,
                inputMethod: 'topic'
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        const result = await response.json();
        return result.outline;
    }

    // 7. NEW: Generate outline from any input type
    async function generateOutlineFromInput(topic, slideCount, inputMethod, contentData = null) {
        const requestData = {
            topic: topic,
            slideCount: slideCount,
            inputMethod: inputMethod
        };

        // Add content data for text/document methods
        if (contentData) {
            if (inputMethod === 'text') {
                requestData.textContent = contentData.full_text;
                requestData.textStats = contentData.analysis;
            } else if (inputMethod === 'document') {
                requestData.documentContent = contentData.full_text;
                requestData.documentStats = contentData.analysis;
                requestData.processingMode = window.inputMethodsHandler.getProcessingMode();
            }
        }

        const response = await fetch('/api/generate-outline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        const result = await response.json();
        return result.outline;
    }

    // 8. UPDATED: Enhanced outline approval with input method context
    function showOutlineForApproval(modalContent, outline, topic, slideCount, inputMethod, contentData = null) {
        const slides = outline.slide_structure || [];

        let slidesHtml = '';
        slides.forEach((slide, index) => {
            const keyPointsHtml = slide.key_points ?
                slide.key_points.map(point => `<li>${point}</li>`).join('') : '';

            // Add content preview for text/document methods
            let contentPreview = '';
            if (slide.content_preview && (inputMethod === 'text' || inputMethod === 'document')) {
                contentPreview = `
                <div class="content-preview">
                    <strong>Content Preview:</strong>
                    <p class="preview-text">${slide.content_preview}</p>
                </div>
            `;
            }

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
                    ${contentPreview}
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

        // Add input method context to the summary
        let methodContext = '';
        if (inputMethod === 'text') {
            methodContext = `
            <div class="meta-item">
                <strong>Source:</strong> <span>Text input (${contentData?.analysis?.words || 'N/A'} words)</span>
            </div>
        `;
        } else if (inputMethod === 'document') {
            const processingMode = window.inputMethodsHandler?.getProcessingMode() || 'preserve';
            methodContext = `
            <div class="meta-item">
                <strong>Source:</strong> <span>Document upload (${contentData?.analysis?.words || 'N/A'} words)</span>
            </div>
            <div class="meta-item">
                <strong>Processing Mode:</strong> <span>${getProcessingModeDisplayName(processingMode)}</span>
            </div>
        `;
        }

        modalContent.innerHTML = `
        <div class="outline-modal-header">
            <h2><i class="fas fa-robot"></i> AI Presentation Planner</h2>
            <button class="modal-close" onclick="closeOutlineModal()">&times;</button>
        </div>
        <div class="outline-modal-body">
            <div class="outline-summary">
                <h3>${outline.presentation_meta?.title || topic}</h3>
                <div class="meta-info">
                    <div class="meta-item">
                        <strong>Objective:</strong> <span>${outline.presentation_meta?.objective || 'Comprehensive overview'}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Target Audience:</strong> <span>${outline.presentation_meta?.target_audience || 'General audience'}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Key Message:</strong> <span>${outline.presentation_meta?.key_message || 'Main insights and takeaways'}</span>
                    </div>
                    ${methodContext}
                </div>
            </div>
            
            <div class="outline-slides">
                <h4>Planned Slide Structure (${slides.length} slides)</h4>
                <div class="slides-flow">
                    ${slidesHtml}
                </div>
            </div>
            
            <div class="outline-actions">
                <button class="btn btn-primary" onclick="approveAndGenerateSlides()">
                    <i class="fas fa-check"></i> Looks Great! Generate Slides
                </button>
                <button class="btn btn-secondary" onclick="regenerateOutline()">
                    <i class="fas fa-redo"></i> Regenerate Outline
                </button>
                <button class="btn btn-secondary" onclick="toggleOutlinePreference('${inputMethod}')">
                    <i class="fas fa-cog"></i> Skip Outline Next Time
                </button>
                <button class="btn btn-danger" onclick="closeOutlineModal()">
                    <i class="fas fa-times"></i> Cancel
                </button>
            </div>
        </div>
    `;

        // Store outline and context for later use
        window.currentOutline = outline;
        window.currentInputMethod = inputMethod;
        window.currentContentData = contentData;
    }
    // 9. NEW: Helper functions for display names
    function getInputMethodDisplayName(method) {
        const names = {
            'topic': 'Topic Input',
            'text': 'Text Content',
            'document': 'Document Upload'
        };
        return names[method] || method;
    }

    function getProcessingModeDisplayName(mode) {
        const names = {
            'preserve': 'Preserve Original Content',
            'condense': 'Condense Key Points',
            'generate': 'Generate Enhanced Content'
        };
        return names[mode] || mode;
    }

    function formatContentLength(contentData) {
        if (!contentData || !contentData.analysis) return 'N/A';

        const { words, characters } = contentData.analysis;
        if (words > 1000) {
            return `${Math.round(words / 1000 * 10) / 10}k words`;
        }
        return `${words} words`;
    }

    // 10. NEW: Estimate slide count based on content
    function estimateSlideCount(text) {
        if (!text) return 5;

        const wordCount = text.split(' ').length;

        if (wordCount < 200) return 3;
        if (wordCount < 500) return 4;
        if (wordCount < 1000) return 5;
        if (wordCount < 1500) return 6;
        if (wordCount < 2500) return 7;
        return Math.min(8, Math.max(7, Math.ceil(wordCount / 350)));
    }

    // 11. NEW: Toggle outline preference
    function toggleOutlinePreference(inputMethod) {
        const currentPref = getUserPreference(`${inputMethod}_outline`, true);
        const newPref = !currentPref;

        setUserPreference(`${inputMethod}_outline`, newPref);

        const action = newPref ? 'enabled' : 'disabled';
        showNotification(`Outline preview ${action} for ${getInputMethodDisplayName(inputMethod)}`, 'success');

        // Update button text
        const button = document.querySelector('[onclick*="toggleOutlinePreference"]');
        if (button) {
            const icon = newPref ? 'fa-eye-slash' : 'fa-eye';
            const text = newPref ? 'Skip Outline Next Time' : 'Use Outline Next Time';
            button.innerHTML = `<i class="fas ${icon}"></i> ${text}`;
        }
    }

    function showOutlineError(modalContent, errorMessage, inputMethod, contentData = null) {
        modalContent.innerHTML = `
        <div class="outline-modal-header">
            <h2><i class="fas fa-robot"></i> AI Presentation Planner</h2>
            <button class="modal-close" onclick="closeOutlineModal()">&times;</button>
        </div>
        <div class="outline-modal-body">
            <div class="outline-error">
                <div class="error-icon">⚠️</div>
                <h3>Outline Generation Failed</h3>
                <p>${errorMessage}</p>
                <div class="error-details">
                    <p><strong>Input Method:</strong> ${getInputMethodDisplayName(inputMethod)}</p>
                    ${contentData ? `<p><strong>Content Length:</strong> ${formatContentLength(contentData)}</p>` : ''}
                </div>
                <div class="error-actions">
                    <button class="btn btn-primary" onclick="regenerateOutline()">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                    <button class="btn btn-secondary" onclick="proceedWithoutOutline()">
                        <i class="fas fa-forward"></i> Skip Outline & Generate
                    </button>
                    <button class="btn btn-danger" onclick="closeOutlineModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </div>
        </div>
    `;
    }

    // 13. NEW: Proceed without outline (fallback option)
    async function proceedWithoutOutline() {
        const inputMethod = window.currentInputMethod;
        const contentData = window.currentContentData;

        // Close modal
        closeOutlineModal();

        // Show notification
        showNotification('Proceeding with direct generation (no outline)', 'info');

        // Proceed with direct generation
        await handleDirectGeneration(inputMethod, contentData);
    }

    // 14. NEW: Handle direct generation
    async function handleDirectGeneration(inputMethod, contentData = null) {
        let processingMode = 'generate';
        if (inputMethod === 'document') {
            processingMode = window.inputMethodsHandler.getProcessingMode();
        } else if (inputMethod === 'text') {
            processingMode = 'preserve';
        }

        const loadingMessages = {
            topic: 'Generating presentation...',
            text: 'Analyzing text content and preserving original structure...',
            document: `Processing document in ${processingMode} mode and determining optimal slide structure...`
        };

        await executeDirectGeneration(inputMethod, processingMode, loadingMessages[inputMethod]);
    }

    async function approveAndGenerateSlides() {
        if (!window.currentOutline) {
            showNotification('No outline available', 'error');
            return;
        }

        const inputMethod = window.currentInputMethod || 'topic';
        const contentData = window.currentContentData;

        const modalContent = document.querySelector('.outline-modal .outline-modal-body');

        // Show generation progress
        modalContent.innerHTML = `
        <div class="slides-generation">
            <div class="loading-spinner"></div>
            <h3>Generating your presentation...</h3>
            <p>Creating slides based on the approved outline using ${getInputMethodDisplayName(inputMethod)}</p>
            <div class="generation-progress">
                <div class="progress-bar">
                    <div class="progress-fill" id="generation-progress-fill"></div>
                </div>
                <div class="progress-text" id="generation-progress-text">Preparing slide generation...</div>
            </div>
        </div>
    `;

        try {
            // Generate slides from outline with content context
            const result = await generateSlidesFromApprovedOutline(window.currentOutline, contentData);

            // Update application state
            window.appState.slides = result.slides;
            window.appState.templateId = window.selectedTemplateId;
            window.appState.topic = window.currentOutline.presentation_meta?.title ||
                document.getElementById('topic').value.trim();
            window.appState.currentSlideIndex = 0;
            window.appState.editMode = false;
            window.appState.isModified = true;
            window.appState.generationMethod = `${inputMethod}-with-outline`;
            window.appState.outline = window.currentOutline;
            window.appState.inputMethod = inputMethod;

            // Add content data to state for reference
            if (contentData) {
                window.appState.sourceContent = contentData;
            }

            // Close modal
            closeOutlineModal();

            // Render slides
            renderSlidesList();
            renderCurrentSlide();

            // Enable buttons
            document.getElementById('export-btn').disabled = false;
            document.getElementById('save-btn').disabled = false;
            updateSaveButtonLabel();

            // Show success notification
            const methodText = getInputMethodDisplayName(inputMethod);
            showNotification(
                `Presentation generated successfully from ${methodText}! (${result.slides.length} slides created from outline)`,
                'success',
                7000
            );

            // Track successful generation
            trackOutlineEvent('slides_generated_from_outline', {
                input_method: inputMethod,
                slide_count: result.slides.length,
                outline_approved: true
            });

        } catch (error) {
            console.error('Error generating slides from outline:', error);
            showOutlineError(modalContent, error.message || 'Failed to generate slides from outline', inputMethod, contentData);
        }
    }

    async function generateSlidesFromApprovedOutline(outline, contentData = null) {
        const requestData = {
            outline: outline,
            template: window.selectedTemplateId
        };

        // Add content data for context-aware generation
        if (contentData) {
            requestData.contentData = contentData;
            requestData.processingMode = window.inputMethodsHandler?.getProcessingMode() || 'preserve';
        }

        const response = await fetch('/api/generate-from-outline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        return await response.json();
    }
    function addOutlinePreferenceIndicators() {
        const methodTabs = document.querySelectorAll('.method-tab');

        methodTabs.forEach(tab => {
            const method = tab.dataset.method;
            if (method && method !== 'topic') {
                const useOutline = getUserPreference(`${method}_outline`, true);

                // Add outline indicator
                let indicator = tab.querySelector('.outline-indicator');
                if (!indicator) {
                    indicator = document.createElement('span');
                    indicator.className = 'outline-indicator';
                    tab.appendChild(indicator);
                }

                indicator.innerHTML = useOutline ?
                    '<i class="fas fa-list-alt" title="Outline preview enabled"></i>' :
                    '<i class="fas fa-fast-forward" title="Direct generation"></i>';
                indicator.className = `outline-indicator ${useOutline ? 'enabled' : 'disabled'}`;
            }
        });
    }

    // 19. NEW: Initialize enhanced outline system
    function initializeEnhancedOutlineSystem() {
        // Add preference indicators
        addOutlinePreferenceIndicators();

        // Listen for input method changes to update indicators
        document.addEventListener('input-method-changed', () => {
            setTimeout(addOutlinePreferenceIndicators, 100);
        });

        // Setup keyboard shortcuts
        setupOutlineKeyboardShortcuts();

        // Track system initialization
        trackOutlineEvent('enhanced_system_initialized');
    }


    async function regenerateOutline() {
        const inputMethod = window.currentInputMethod || 'topic';
        const contentData = window.currentContentData;

        let topic, slideCount;

        // Get current data based on input method
        switch (inputMethod) {
            case 'topic':
                topic = document.getElementById('topic').value.trim();
                slideCount = parseInt(document.getElementById('slide-count').value, 10) || 5;
                break;
            case 'text':
            case 'document':
                topic = document.getElementById('topic').value.trim() ||
                    extractTopicFromContent(contentData) ||
                    `${getInputMethodDisplayName(inputMethod)} Presentation`;
                slideCount = estimateSlideCount(contentData?.full_text || '');
                break;
        }

        const modalContent = document.querySelector('.outline-modal .outline-modal-body');

        // Show loading state
        modalContent.innerHTML = `
        <div class="outline-loading">
            <div class="loading-spinner"></div>
            <h3>Regenerating presentation outline...</h3>
            <p>Creating a fresh structure with new ideas and perspectives...</p>
            <div class="loading-details">
                <div class="detail-item">
                    <span class="detail-label">Input Method</span>
                    <span class="detail-value">${getInputMethodDisplayName(inputMethod)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Topic</span>
                    <span class="detail-value">${topic}</span>
                </div>
            </div>
        </div>
    `;

        try {
            const outline = await generateOutlineFromInput(topic, slideCount, inputMethod, contentData);
            showOutlineForApproval(modalContent, outline, topic, slideCount, inputMethod, contentData);

            // Track regeneration
            trackOutlineEvent('outline_regenerated', {
                input_method: inputMethod,
                slide_count: slideCount
            });

        } catch (error) {
            console.error('Error regenerating outline:', error);
            showOutlineError(modalContent, error.message, inputMethod, contentData);
        }
    }

    // 10. NEW: Close outline modal
    function closeOutlineModal() {
        const modal = document.getElementById('outline-generation-modal');
        if (modal?.parentNode) {
            document.body.removeChild(modal);
        }

        // Clean up stored data
        delete window.currentOutline;
    }

    // 11. NEW: Get layout display name
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



    // Add global functions to window for onclick handlers
    window.approveAndGenerateSlides = approveAndGenerateSlides;
    window.regenerateOutline = regenerateOutline;
    window.closeOutlineModal = closeOutlineModal;


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
            bulletFields += createFormField(`Bullet ${i + 1}`, `bullet-${i}`, bullets[i] || '');
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
                <h5>Feature ${i + 1}</h5>
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
            switch (layout) {
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

    window.ppgLayouts.collectFormData = function (layout) {
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


    // FIXED RENDER FUNCTIONS - Replace your existing functions with these:

    function renderSlidesList() {
        const slidesList = document.getElementById('slides-list');

        if (!slidesList) {
            console.error('❌ slides-list element not found');
            return;
        }

        if (!window.appState || !window.appState.slides || window.appState.slides.length === 0) {
            slidesList.innerHTML = `
            <div class="slides-placeholder">
                Slides will appear here after generation
            </div>
        `;
            return;
        }

        console.log('🎨 Rendering slides list with', window.appState.slides.length, 'slides');

        let slidesHtml = '';

        window.appState.slides.forEach((slide, index) => {
            const isActive = index === window.appState.currentSlideIndex;

            try {
                // Use fallback if ppgLayouts isn't available
                let previewHtml;
                if (window.ppgLayouts && typeof window.ppgLayouts.renderPreview === 'function') {
                    previewHtml = window.ppgLayouts.renderPreview(slide.layout, slide.content, window.appState.templateId);
                } else {
                    previewHtml = `
                    <div class="slide-preview-fallback">
                        <h4>${slide.content.title || `Slide ${index + 1}`}</h4>
                        <p>Layout: ${slide.layout}</p>
                        <small>${Object.keys(slide.content).length} content fields</small>
                    </div>
                `;
                }

                slidesHtml += `
                <div class="slide-thumbnail ${isActive ? 'active' : ''}" data-index="${index}">
                    <div class="slide-thumbnail-content">
                        ${previewHtml}
                    </div>
                    <div class="slide-actions">
                        <span class="slide-number">Slide ${index + 1}</span>
                        <button class="btn-icon delete-slide" data-index="${index}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            } catch (error) {
                console.error(`❌ Error rendering slide ${index + 1}:`, error);
                slidesHtml += `
                <div class="slide-thumbnail ${isActive ? 'active' : ''}" data-index="${index}">
                    <div class="slide-thumbnail-content">
                        <div class="slide-error">
                            <h4>Slide ${index + 1}</h4>
                            <p>Error rendering preview</p>
                        </div>
                    </div>
                </div>
            `;
            }
        });

        slidesList.innerHTML = slidesHtml;

        // Add click events to thumbnails
        const thumbnails = slidesList.querySelectorAll('.slide-thumbnail');
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', () => {
                const index = parseInt(thumbnail.dataset.index);
                if (window.appState.currentSlideIndex !== index) {
                    if (window.appState.editMode) {
                        const confirmChange = confirm('You have unsaved changes. Continue without saving?');
                        if (!confirmChange) return;
                    }

                    window.appState.currentSlideIndex = index;
                    renderCurrentSlide();
                    renderSlidesList(); // Re-render to update active state
                }
            });
        });

        // Add click events to delete buttons
        const deleteButtons = slidesList.querySelectorAll('.delete-slide');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(button.dataset.index);
                deleteSlide(index);
            });
        });

        console.log('✅ Slides list rendered successfully');
    }

    function renderCurrentSlide() {
        if (!window.appState || !window.appState.slides || window.appState.slides.length === 0) {
            console.warn('⚠️ No slides to render');
            return;
        }

        const slideData = window.appState.slides[window.appState.currentSlideIndex];
        const slidePreview = document.getElementById('slide-preview');

        if (!slidePreview) {
            console.error('❌ slide-preview element not found');
            return;
        }

        if (!slideData) {
            slidePreview.innerHTML = `
            <div class="placeholder-message">
                No slide data available for slide ${window.appState.currentSlideIndex + 1}
            </div>
        `;
            return;
        }

        if (window.appState.editMode && document.getElementById('edit-form')?.classList.contains('hidden') === false) {
            return;
        }

        try {
            // Use fallback if ppgLayouts isn't available
            let slideHtml;
            if (window.ppgLayouts && typeof window.ppgLayouts.renderPreview === 'function') {
                slideHtml = window.ppgLayouts.renderPreview(slideData.layout, slideData.content, window.appState.templateId);
            } else {
                // Enhanced fallback with better formatting
                slideHtml = createFallbackSlidePreview(slideData);
            }

            slidePreview.innerHTML = slideHtml;

            // Call other render functions if they exist
            if (typeof renderSlideControls === 'function') {
                renderSlideControls();
            }
            if (typeof updateEditControls === 'function') {
                updateEditControls();
            }

            console.log(`✅ Rendered slide ${window.appState.currentSlideIndex + 1}`);

        } catch (error) {
            console.error('❌ Error rendering current slide:', error);
            slidePreview.innerHTML = `
            <div class="slide-error">
                <h3>Error Rendering Slide</h3>
                <p><strong>Layout:</strong> ${slideData.layout}</p>
                <p><strong>Error:</strong> ${error.message}</p>
                <details>
                    <summary>Slide Content</summary>
                    <pre>${JSON.stringify(slideData.content, null, 2)}</pre>
                </details>
            </div>
        `;
        }
    }

    // Enhanced fallback slide preview
    function createFallbackSlidePreview(slideData) {
        const content = slideData.content || {};
        const layout = slideData.layout;

        let contentHtml = '';

        switch (layout) {
            case 'titleOnly':
                contentHtml = `
                <h1 class="slide-title">${content.title || 'Title'}</h1>
                <h2 class="slide-subtitle">${content.subtitle || 'Subtitle'}</h2>
            `;
                break;

            case 'titleAndBullets':
                const bullets = content.bullets || [];
                const bulletsHtml = bullets.map(bullet => `<li>${bullet}</li>`).join('');
                contentHtml = `
                <h2 class="slide-title">${content.title || 'Title'}</h2>
                <ul class="slide-bullets">${bulletsHtml}</ul>
            `;
                break;

            case 'imageAndParagraph':
                contentHtml = `
                <h2 class="slide-title">${content.title || 'Title'}</h2>
                <div class="slide-image-placeholder">[Image: ${content.imageDescription || 'Image'}]</div>
                <p class="slide-paragraph">${content.paragraph || 'Paragraph content'}</p>
            `;
                break;

            case 'quote':
                contentHtml = `
                <blockquote class="slide-quote">
                    "${content.quote || 'Quote text'}"
                    <cite>— ${content.author || 'Author'}</cite>
                </blockquote>
            `;
                break;

            case 'twoColumn':
                contentHtml = `
                <h2 class="slide-title">${content.title || 'Title'}</h2>
                <div class="slide-two-columns">
                    <div class="slide-column">
                        <h3>${content.column1Title || 'Column 1'}</h3>
                        <p>${content.column1Content || 'Column 1 content'}</p>
                    </div>
                    <div class="slide-column">
                        <h3>${content.column2Title || 'Column 2'}</h3>
                        <p>${content.column2Content || 'Column 2 content'}</p>
                    </div>
                </div>
            `;
                break;

            case 'conclusion':
                const nextSteps = content.nextSteps || [];
                const stepsHtml = nextSteps.map(step => `<li>${step}</li>`).join('');
                contentHtml = `
                <h2 class="slide-title">${content.title || 'Conclusion'}</h2>
                <p class="slide-summary">${content.summary || 'Summary'}</p>
                <h3>Next Steps:</h3>
                <ul class="slide-next-steps">${stepsHtml}</ul>
            `;
                break;

            default:
                contentHtml = `
                <h2 class="slide-title">${content.title || 'Slide Title'}</h2>
                <p><strong>Layout:</strong> ${layout}</p>
                <div class="slide-content-debug">
                    <details>
                        <summary>Content Details</summary>
                        <pre>${JSON.stringify(content, null, 2)}</pre>
                    </details>
                </div>
            `;
        }

        return `
        <div class="fallback-slide-display" data-layout="${layout}">
            ${contentHtml}
            <div class="slide-info">
                <small>Slide ${window.appState.currentSlideIndex + 1} of ${window.appState.slides.length} • Layout: ${layout}</small>
            </div>
        </div>
    `;
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
        switch (appState.editMode) {
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
        modalContent.querySelector('#change-layout-btn').addEventListener('click', function () {
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

        modalContent.querySelector('#cancel-layout-btn').addEventListener('click', function () {
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
            saveBtn.addEventListener('click', function () {
                saveCurrentEdit(currentSlide, modalOverlay);
            });
        }

        const cancelBtn = modalContent.querySelector('#cancel-edit-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function () {
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
        modalContent.querySelector('#add-slide-with-layout-btn').addEventListener('click', function () {
            addSlideWithSelectedLayout(modalOverlay);
        });

        modalContent.querySelector('#cancel-add-slide-btn').addEventListener('click', function () {
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

        switch (layout) {
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



    // function initializeEditButtons() {
    //     // Add click handler for the Edit Content button
    //     const editContentBtn = document.getElementById('edit-content-btn');
    //     if (editContentBtn) {
    //         editContentBtn.addEventListener('click', showEditForm);
    //     }

    //     // Add click handler for the Change Layout button
    //     const changeLayoutBtn = document.getElementById('change-layout-btn');
    //     if (changeLayoutBtn) {
    //         changeLayoutBtn.addEventListener('click', changeSlideLayout);
    //     }

    //     // Add click handler for the Add New Slide button
    //     const addSlideBtn = document.getElementById('add-slide-btn');
    //     if (addSlideBtn) {
    //         addSlideBtn.addEventListener('click', addNewSlide);
    //     }

    //     // Add click handler for the Delete Slide button
    //     const deleteSlideBtn = document.getElementById('delete-slide-btn');
    //     if (deleteSlideBtn) {
    //         deleteSlideBtn.addEventListener('click', deleteCurrentSlide);
    //     }

    //     // Add click handler for export button
    //     const exportBtn = document.getElementById('export-btn');
    //     if (exportBtn) {
    //         exportBtn.addEventListener('click', handleExport);
    //     }

    //     // Add click handler for save button
    //     const saveBtn = document.getElementById('save-btn');
    //     if (saveBtn) {
    //         saveBtn.addEventListener('click', handleSave);
    //     }

    //     // Add click handler for previous slide button
    //     const prevSlideBtn = document.getElementById('prev-slide');
    //     if (prevSlideBtn) {
    //         prevSlideBtn.addEventListener('click', showPreviousSlide);
    //     }

    //     // Add click handler for next slide button
    //     const nextSlideBtn = document.getElementById('next-slide');
    //     if (nextSlideBtn) {
    //         nextSlideBtn.addEventListener('click', showNextSlide);
    //     }

    //     // Keyboard navigation
    //     document.addEventListener('keydown', (e) => {
    //         if (window.appState.slides.length <= 1 || window.appState.editMode) return;

    //         // Left arrow key
    //         if (e.key === 'ArrowLeft' && window.appState.currentSlideIndex > 0) {
    //             showPreviousSlide();
    //         }
    //         // Right arrow key
    //         else if (e.key === 'ArrowRight' && window.appState.currentSlideIndex < window.appState.slides.length - 1) {
    //             showNextSlide();
    //         }
    //     });}
});


