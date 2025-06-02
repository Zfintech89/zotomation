class InputMethodsHandler {
    constructor() {
        this.currentMethod = 'topic';
        this.textStats = { chars: 0, words: 0, suggestedSlides: 5 };
        this.processedContent = null;
        this.extractedText = null;
        this.processingMode = 'preserve'; // Default processing mode
        this.init();
    }

    init() {
        this.setupTabSwitching();
        this.setupTextAnalysis();
        this.setupFileUpload();
    }

    setupTabSwitching() {
        const tabs = document.querySelectorAll('.method-tab');
        const panels = document.querySelectorAll('.input-panel');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const method = tab.dataset.method;
                this.switchMethod(method);
            });
        });
    }

    switchMethod(method) {
        if (this.currentMethod === method) return;

        // Clear data from ALL other methods when switching
        this.clearAllMethodsExcept(method);

        // Update tabs
        document.querySelectorAll('.method-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.method === method);
        });

        // Update panels
        document.querySelectorAll('.input-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        const targetPanel = document.getElementById(`${method}-input-panel`);
        if (targetPanel) {
            targetPanel.classList.add('active');
        }

        this.currentMethod = method;
        this.updateGenerateButton();

        console.log(`Switched to ${method} input method`);
    }

    clearAllMethodsExcept(activeMethod) {
        // Clear topic field (except when switching to topic)
        if (activeMethod !== 'topic') {
            const topicInput = document.getElementById('topic');
            if (topicInput) {
                topicInput.value = '';
            }
        }
        
        // Clear text area and stats (except when switching to text)
        if (activeMethod !== 'text') {
            const textArea = document.getElementById('content-text');
            if (textArea) {
                textArea.value = '';
            }
            this.textStats = { chars: 0, words: 0, suggestedSlides: 5 };
            this.updateTextStats();
        }
        
        // Clear document upload (except when switching to document)
        if (activeMethod !== 'document') {
            this.clearFile();
            this.showUploadArea();
        }
    }

    clearMethodData(method) {
        switch (method) {
            case 'topic':
                const topicInput = document.getElementById('topic');
                if (topicInput) {
                    topicInput.value = '';
                }
                break;
                
            case 'text':
                const textArea = document.getElementById('content-text');
                if (textArea) {
                    textArea.value = '';
                }
                this.textStats = { chars: 0, words: 0, suggestedSlides: 5 };
                this.updateTextStats();
                break;
                
            case 'document':
                this.clearFile();
                this.showUploadArea();
                break;
        }
    }

    showUploadArea() {
        const uploadArea = document.getElementById('upload-area');
        if (uploadArea) {
            uploadArea.classList.remove('hidden');
            uploadArea.style.display = '';
        }
    }

    hideUploadArea() {
        const uploadArea = document.getElementById('upload-area');
        if (uploadArea) {
            uploadArea.classList.add('hidden');
        }
    }

    setupTextAnalysis() {
        const textArea = document.getElementById('content-text');
        if (!textArea) return;

        textArea.addEventListener('input', () => {
            this.analyzeText(textArea.value);
        });

        textArea.addEventListener('paste', () => {
            setTimeout(() => this.analyzeText(textArea.value), 10);
        });
    }

    analyzeText(text) {
        const chars = text.length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;

        let suggestedSlides = 5;
        if (words < 100) {
            suggestedSlides = 3;
        } else if (words < 300) {
            suggestedSlides = 4;
        } else if (words < 600) {
            suggestedSlides = 5;
        } else if (words < 1000) {
            suggestedSlides = 6;
        } else if (words < 1500) {
            suggestedSlides = 7;
        } else {
            suggestedSlides = 8;
        }

        this.textStats = { chars, words, suggestedSlides };
        this.updateTextStats();

        const slideCountInput = document.getElementById('slide-count');
        if (slideCountInput && this.currentMethod === 'text') {
            slideCountInput.value = suggestedSlides;
        }
    }

    updateTextStats() {
        const charCount = document.getElementById('char-count');
        const wordCount = document.getElementById('word-count');
        const suggestedSlides = document.getElementById('suggested-slides');

        if (charCount) charCount.textContent = `${this.textStats.chars.toLocaleString()} characters`;
        if (wordCount) wordCount.textContent = `${this.textStats.words.toLocaleString()} words`;
        if (suggestedSlides) suggestedSlides.textContent = `Suggested: ${this.textStats.suggestedSlides} slides`;
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');

        if (!uploadArea || !fileInput) return;

        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileUpload(file);
            }
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        console.log('File selected:', file.name);

        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        const allowedExts = ['.pdf', '.docx', '.doc', '.txt'];

        if (!allowedTypes.includes(file.type) && !allowedExts.includes(fileExt)) {
            this.showNotification('Please upload a PDF, DOCX, DOC, or TXT file.', 'error');
            return;
        }

        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            this.showNotification('File size must be less than 50MB.', 'error');
            return;
        }

        this.showFilePreview(file);
        this.showProcessingIndicator('Extracting text from document...');

        try {
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

            console.log('Document processed successfully:', result);

            this.processedContent = result.content;
            this.extractedText = result.extracted_text || result.content.full_text || '';
            
            // Show processing mode selection dropdown
            this.showProcessingModeSelection();

            this.updateFileProcessingResults(result);

            // Hide upload area after successful upload
            this.hideUploadArea();

            this.showNotification(`Document processed successfully! Choose processing mode below.`, 'success');

        } catch (error) {
            console.error('Document processing error:', error);
            this.showNotification(error.message || 'Failed to process document', 'error');
            this.clearFile();
        } finally {
            this.hideProcessingIndicator();
        }
    }

    showFilePreview(file) {
        const preview = document.getElementById('file-preview');
        if (!preview) return;

        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);

        preview.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-file-${this.getFileIcon(file.name)}"></i>
                </div>
                <div class="file-details">
                    <h4>${file.name}</h4>

                </div>
                <button class="btn btn-sm btn-danger" onclick="window.inputMethodsHandler.clearFile()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        preview.classList.remove('hidden');
    }

    // Show processing mode selection as dropdown
    showProcessingModeSelection() {
        const extractedTextContainer = document.getElementById('extracted-text-container');
        if (!extractedTextContainer) return;

        // Check if processing options already exist
        if (document.getElementById('processing-mode-dropdown-container')) return;

        const processingDropdownHtml = `
            <div id="processing-mode-dropdown-container" class="processing-mode-dropdown-container">
                <h4><i class=""></i> Content Processing Settings</h4>
                            <div class="processing-mode-selection-wrapper">
                    <div class="processing-mode-toggle-button toggle-icon" id="processing-mode-toggle-button">
                      
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="processing-mode-panel" id="processing-mode-panel">
                        <div class="processing-mode-grid" id="processing-mode-grid">
                            <div class="processing-mode-option selected" data-mode="preserve">
                                <div class="mode-icon">🔒</div>
                                <div class="mode-details">
                                    <span class="mode-title">Preserve Original</span>
                                </div>
                            </div>
                            <div class="processing-mode-option" data-mode="condense">
                                <div class="mode-icon">📝</div>
                                <div class="mode-details">
                                    <span class="mode-title">Condense Content</span>
                                </div>
                            </div>
                            <div class="processing-mode-option" data-mode="generate">
                                <div class="mode-icon">🎨</div>
                                <div class="mode-details">
                                    <span class="mode-title">Generate Enhanced</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        extractedTextContainer.innerHTML = processingDropdownHtml;
        extractedTextContainer.classList.remove('hidden');

        // Set up dropdown functionality
        this.setupProcessingModeDropdown();
    }

    // Setup processing mode dropdown
    setupProcessingModeDropdown() {
        const toggleButton = document.getElementById('processing-mode-toggle-button');
        const panel = document.getElementById('processing-mode-panel');
        const options = document.querySelectorAll('.processing-mode-option');
        
        // Hide panel initially
        panel.style.display = 'none';
        
        // Toggle function
        const togglePanel = () => {
            const isVisible = panel.style.display !== 'none';
            panel.style.display = isVisible ? 'none' : 'block';
            
            // Update toggle icon
            const toggleIcon = document.querySelector('#processing-mode-dropdown-container .toggle-icon');
            if (toggleIcon) {
                toggleIcon.textContent = isVisible ? '▼' : '▲';
            }
        };
        
        // Add click event to toggle button
        if (toggleButton) {
            toggleButton.addEventListener('click', togglePanel);
        }
        
        // Add click events to mode options
        options.forEach(option => {
            option.addEventListener('click', () => {
                const mode = option.dataset.mode;
                
                // Remove selected class from all options
                options.forEach(opt => opt.classList.remove('selected'));
                
                // Add selected class to clicked option
                option.classList.add('selected');
                
                // Update the processing mode
                this.processingMode = mode;
                
                // Update the toggle button text
                const modeTitle = option.querySelector('.mode-title').textContent;
                const modeDesc = option.querySelector('.mode-description').textContent;
                
                const selectedName = document.getElementById('selected-processing-mode-name');
                const selectedDesc = document.getElementById('selected-processing-mode-desc');
                
                if (selectedName) selectedName.textContent = `Processing Mode: ${modeTitle}`;
                if (selectedDesc) selectedDesc.textContent = modeDesc;
                
                // Update info text
                this.updateProcessingModeInfo(mode);
                
                // Close the panel after selection
                panel.style.display = 'none';
                
                // Update toggle icon
                const toggleIcon = document.querySelector('#processing-mode-dropdown-container .toggle-icon');
                if (toggleIcon) {
                    toggleIcon.textContent = '▼';
                }
                
                console.log(`Processing mode changed to: ${mode}`);
            });
        });
        
        // Close panel when clicking outside
        document.addEventListener('click', (event) => {
            const container = document.getElementById('processing-mode-dropdown-container');
            if (container && !container.contains(event.target)) {
                panel.style.display = 'none';
                
                // Update toggle icon
                const toggleIcon = document.querySelector('#processing-mode-dropdown-container .toggle-icon');
                if (toggleIcon) {
                    toggleIcon.textContent = '▼';
                }
            }
        });
        
        // Show initial info for default mode
        this.updateProcessingModeInfo('preserve');
    }

    // Update processing mode info
    updateProcessingModeInfo(mode) {
        const infoTexts = {
            preserve: "✅ Original text will be kept as much as possible. Minimal changes for slide formatting only.",
            condense: "📝 Content will be summarized while maintaining key points and important details.",
            generate: "🎨 Content will be used as inspiration to create enhanced, AI-generated slide content."
        };
        
        const infoElement = document.getElementById('processing-mode-info');
        if (infoElement) {
            const infoText = infoElement.querySelector('.info-text');
            if (infoText) {
                infoText.textContent = infoTexts[mode] || infoTexts.preserve;
            }
        }
    }

    updateFileProcessingResults(result) {
        const statusElement = document.getElementById('processing-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="processing-results">
                    <div class="stats-row">
                        <span class="stat-item">${result.stats.words.toLocaleString()} words</span>
                        <span class="stat-item">${result.stats.characters.toLocaleString()} characters</span>
                    </div>
                    <div class="stats-row">
                        <span class="stat-item">${result.stats.paragraphs} paragraphs</span>
                        <span class="stat-item">Ready for processing</span>
                    </div>
                    <div class="readability-indicator">
                        <span class="readability ${result.stats.readability}">
                            ${result.stats.readability.charAt(0).toUpperCase() + result.stats.readability.slice(1)} readability
                        </span>
                    </div>
                </div>
            `;
        }
    }

    showProcessingIndicator(message) {
        const statusElement = document.getElementById('processing-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="processing-indicator">
                    <div class="spinner"></div>
                    <span>${message}</span>
                </div>
            `;
        }
    }

    hideProcessingIndicator() {
        // Processing indicator will be replaced by results or cleared
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'pdf': return 'pdf';
            case 'doc':
            case 'docx': return 'word';
            case 'txt': return 'alt';
            default: return 'file';
        }
    }

    clearFile() {
        const fileInput = document.getElementById('file-input');
        const preview = document.getElementById('file-preview');
        const extractedTextContainer = document.getElementById('extracted-text-container');
        const processingDropdown = document.getElementById('processing-mode-dropdown-container');

        if (fileInput) fileInput.value = '';
        if (preview) preview.classList.add('hidden');
        if (extractedTextContainer) {
            extractedTextContainer.classList.add('hidden');
            extractedTextContainer.innerHTML = ''; // Clear all content
        }
        if (processingDropdown) processingDropdown.remove();

        this.processedContent = null;
        this.extractedText = null;
        this.processingMode = 'preserve'; // Reset to default

        // Show upload area again when clearing file
        this.showUploadArea();
    }

    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-btn');
        if (!generateBtn) return;

        const buttonTexts = {
            topic: '<i class="fas fa-magic"></i> Generate Presentation',
            text: '<i class="fas fa-file-text"></i> Generate from Text',
            document: '<i class="fas fa-file-upload"></i> Generate from Document'
        };

        generateBtn.innerHTML = buttonTexts[this.currentMethod];
    }

    getCurrentMethod() {
        return this.currentMethod;
    }

    getTextContent() {
        // Only return text content if we're in text mode
        if (this.currentMethod !== 'text') {
            return '';
        }
        const textArea = document.getElementById('content-text');
        return textArea ? textArea.value.trim() : '';
    }

    getProcessedContent() {
        // Only return processed content if we're in document mode
        if (this.currentMethod !== 'document') {
            return null;
        }
        return this.processedContent;
    }

    getProcessingMode() {
        return this.processingMode || 'preserve';
    }

    async processTextContent() {
        // Ensure we're in text mode
        if (this.currentMethod !== 'text') {
            throw new Error('Not in text input mode');
        }

        const textContent = this.getTextContent();

        if (!textContent) {
            throw new Error('Please paste some text content');
        }

        if (textContent.length < 50) {
            throw new Error('Please provide more text content (at least 50 characters)');
        }

        try {
            const response = await fetch('/api/process-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: textContent
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Text processing failed');
            }

            this.processedContent = result.content;
            return result;

        } catch (error) {
            console.error('Text processing error:', error);
            throw error;
        }
    }

    validateCurrentInput() {
        // Clear data from inactive methods first
        this.clearInactiveMethods();

        switch (this.currentMethod) {
            case 'topic':
                const topic = document.getElementById('topic').value.trim();
                return topic ? { valid: true } : { valid: false, message: 'Please enter a presentation topic' };

            case 'text':
                const text = this.getTextContent();
                if (!text) {
                    return { valid: false, message: 'Please paste some text content' };
                }
                if (text.length < 50) {
                    return { valid: false, message: 'Please provide more text content (at least 50 characters)' };
                }
                return { valid: true };

            case 'document':
                const fileInput = document.getElementById('file-input');
                const hasProcessedContent = this.processedContent !== null;
                const hasExtractedText = this.extractedText !== null;

                if (!fileInput || !fileInput.files.length) {
                    return { valid: false, message: 'Please upload a document' };
                }

                if (!hasProcessedContent || !hasExtractedText) {
                    return { valid: false, message: 'Document is still processing or failed to process' };
                }

                console.log('Document validation passed:', {
                    hasFile: !!fileInput.files.length,
                    hasProcessedContent,
                    hasExtractedText,
                    textLength: this.extractedText?.length || 0
                });

                return { valid: true };

            default:
                return { valid: false, message: 'Invalid input method' };
        }
    }

    clearInactiveMethods() {
        const activeMethod = this.currentMethod;
        
        if (activeMethod !== 'topic') {
            const topicInput = document.getElementById('topic');
            if (topicInput) {
                topicInput.value = '';
            }
        }
        
        if (activeMethod !== 'text') {
            const textArea = document.getElementById('content-text');
            if (textArea) {
                textArea.value = '';
            }
            this.textStats = { chars: 0, words: 0, suggestedSlides: 5 };
        }
        
        if (activeMethod !== 'document') {
            this.processedContent = null;
            this.extractedText = null;
        }
    }

    showNotification(message, type = 'info') {
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

class DocumentMemoryStore {
    constructor() {
        this.reset();
    }
    
    reset() {
        this.currentFile = null;
        this.extractedContent = null;
        this.processingMode = 'preserve';
        this.fileStats = null;
        this.processingResults = null;
    }
    
    setFile(file) {
        this.currentFile = file;
    }
    
    setExtractedContent(content) {
        this.extractedContent = content;
    }
    
    setProcessingMode(mode) {
        this.processingMode = mode;
        console.log(`Processing mode set to: ${mode}`);
    }
    
    setFileStats(stats) {
        this.fileStats = stats;
    }
    
    setProcessingResults(results) {
        this.processingResults = results;
    }
    
    getProcessedContent() {
        return this.extractedContent;
    }
    
    getProcessingMode() {
        return this.processingMode;
    }
    
    hasDocument() {
        return this.currentFile !== null && this.extractedContent !== null;
    }
    
    getFileInfo() {
        return {
            file: this.currentFile,
            stats: this.fileStats,
            content: this.extractedContent,
            processingMode: this.processingMode
        };
    }
}

window.documentStore = new DocumentMemoryStore();

function openFileModal() {
    const modal = document.getElementById('file-upload-modal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeFileModal() {
    const modal = document.getElementById('file-upload-modal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function removeFile() {
    const fileDisplay = document.getElementById('file-display-compact');
    if (fileDisplay) {
        fileDisplay.classList.add('hidden');
    }
    
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.value = '';
    }
    
    const extractedTextContainer = document.getElementById('extracted-text-container');
    if (extractedTextContainer) {
        extractedTextContainer.classList.add('hidden');
    }
    
    window.documentStore.reset();
    
    console.log('File removed and memory cleared');
}

function updateFileDisplay(file, stats) {
    const fileDisplay = document.getElementById('file-display-compact');
    const fileName = document.getElementById('file-name-display');
    const fileStats = document.getElementById('file-stats-display');
    const fileIcon = document.getElementById('file-icon-display');
    
    if (fileDisplay && fileName && fileStats && fileIcon) {
        fileName.textContent = file.name;
        fileStats.textContent = `${stats.words} words • ${stats.characters} characters • Ready for processing`;
        
        const extension = file.name.split('.').pop().toLowerCase();
        fileIcon.className = 'file-icon-compact';
        
        if (extension === 'pdf') {
            fileIcon.classList.add('pdf');
            fileIcon.innerHTML = '<i class="fas fa-file-pdf"></i>';
        } else if (['doc', 'docx'].includes(extension)) {
            fileIcon.classList.add('word');
            fileIcon.innerHTML = '<i class="fas fa-file-word"></i>';
        } else {
            fileIcon.classList.add('text');
            fileIcon.innerHTML = '<i class="fas fa-file-text"></i>';
        }
        
        fileDisplay.classList.remove('hidden');
        
        window.documentStore.setFile(file);
        window.documentStore.setFileStats(stats);
    }
}

function useDocument() {
    const processingMode = getSelectedProcessingMode();
    
    if (window.documentStore.currentFile) {
        window.documentStore.setProcessingMode(processingMode);
        
        const fileStats = document.getElementById('file-stats-display');
        if (fileStats) {
            const stats = window.documentStore.fileStats;
            const modeLabel = {
                'preserve': 'Preserve Mode',
                'condense': 'Condense Mode', 
                'generate': 'AI Enhanced Mode'
            }[processingMode] || 'Ready';
            
            fileStats.textContent = `${stats.words} words • ${stats.characters} characters • ${modeLabel}`;
        }
        
        updateFileDisplay(window.documentStore.currentFile, window.documentStore.fileStats);
        
        closeFileModal();
        
        console.log('Document ready for generation:', {
            mode: processingMode,
            hasContent: !!window.documentStore.extractedContent
        });
    }
}

function toggleProcessingModePanel() {
    const panel = document.getElementById('processing-mode-panel');
    const toggleIcon = document.querySelector('.processing-mode-toggle-button .toggle-icon');
    
    if (panel && toggleIcon) {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        toggleIcon.textContent = isVisible ? '▼' : '▲';
    }
}

function getSelectedProcessingMode() {
    const selectedOption = document.querySelector('.processing-mode-option.selected');
    return selectedOption ? selectedOption.dataset.mode : 'preserve';
}

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.processing-mode-option')) {
            const option = e.target.closest('.processing-mode-option');
            const mode = option.dataset.mode;
            
            document.querySelectorAll('.processing-mode-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            option.classList.add('selected');
            
            const modeName = document.getElementById('selected-processing-mode-name');
            const modeDesc = document.getElementById('selected-processing-mode-desc');
            const modeTitle = option.querySelector('.mode-title').textContent;
            const modeDescription = option.querySelector('.mode-description').textContent;
            
            if (modeName && modeDesc) {
                modeName.textContent = modeTitle;
                modeDesc.textContent = modeDescription;
            }
            
            window.documentStore.setProcessingMode(mode);
            
            document.getElementById('processing-mode-panel').style.display = 'none';
            document.querySelector('.processing-mode-toggle-button .toggle-icon').textContent = '▼';
        }
    });
    
    const improvedTabs = document.querySelectorAll('.method-tab-improved');
    improvedTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            improvedTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            const panels = document.querySelectorAll('.input-panel');
            panels.forEach(panel => panel.classList.remove('active'));
            
            const method = this.dataset.method;
            const targetPanel = document.getElementById(`${method}-input-panel`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
            
            const event = new CustomEvent('input-method-changed', {
                detail: { method: method }
            });
            document.dispatchEvent(event);
        });
    });

    const modal = document.getElementById('file-upload-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeFileModal();
            }
        });
    }
});

if (window.inputMethodsHandler) {
    const originalGetProcessedContent = window.inputMethodsHandler.getProcessedContent;
    const originalGetProcessingMode = window.inputMethodsHandler.getProcessingMode;
    
    window.inputMethodsHandler.getProcessedContent = function() {
        return window.documentStore.getProcessedContent() || originalGetProcessedContent?.call(this);
    };
    
    window.inputMethodsHandler.getProcessingMode = function() {
        return window.documentStore.getProcessingMode() || originalGetProcessingMode?.call(this) || 'preserve';
    };
}

document.addEventListener('DOMContentLoaded', () => {
    if (!window.inputMethodsHandler) {
        window.inputMethodsHandler = new InputMethodsHandler();
    }
});