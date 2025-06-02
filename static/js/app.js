// app.js - Main application logic for the PowerPoint generator with editing functionality

document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const topicInput = document.getElementById('topic');
    const slideCountInput = document.getElementById('slide-count');
    const generateBtn = document.getElementById('generate-btn');
    const exportBtn = document.getElementById('export-btn');
    const slidePreview = document.getElementById('slide-preview');
    const loadingIndicator = document.getElementById('loading');
    const previewSection = document.getElementById('preview-section');
    
    // Create a container for the edit button outside the slide preview
    const editButtonContainer = document.createElement('div');
    editButtonContainer.className = 'edit-controls';
    editButtonContainer.id = 'external-edit-controls';
    editButtonContainer.style.display = 'none'; // Hide initially
    
    // Insert the edit button container right after the slide preview
    slidePreview.parentNode.insertBefore(editButtonContainer, slidePreview.nextSibling);
        setTimeout(() => {
        debugSlideCountInput();
    }, 1000);
    
    // Application state
    let currentState = {
        slides: [],
        templateId: null,
        topic: null,
        currentSlideIndex: 0,
        editMode: false
    };
    
    // Event listeners
    generateBtn.addEventListener('click', handleGenerate);
    exportBtn.addEventListener('click', handleExport);
    function debugSlideCountInput() {
    console.log('=== SLIDE COUNT INPUT DEBUG ===');
    console.log('getElementById("slide-count"):', document.getElementById('slide-count'));
    console.log('querySelector("#slide-count"):', document.querySelector('#slide-count'));
    console.log('querySelector("input[type=number]"):', document.querySelector('input[type="number"]'));
    console.log('All number inputs:', document.querySelectorAll('input[type="number"]'));
    
    const slideCountElement = document.getElementById('slide-count');
    if (slideCountElement) {
        console.log('Slide count value:', slideCountElement.value);
        console.log('Slide count type:', typeof slideCountElement.value);
        console.log('Parsed value:', parseInt(slideCountElement.value, 10));
    } else {
        console.log('Slide count input NOT FOUND!');
        console.log('Available form inputs:');
        document.querySelectorAll('input').forEach((input, index) => {
            console.log(`Input ${index}:`, {
                id: input.id,
                name: input.name,
                type: input.type,
                value: input.value
            });
        });
    }
    console.log('=== END DEBUG ===');
}
    // Generate slides
async function handleGenerate() {
    const topic = topicInput.value.trim();
    const templateId = window.selectedTemplateId;
    
    // 🔍 DEBUG: Check if slide count input exists
    const slideCountElement = document.getElementById('slide-count');
    console.log('Slide count element found:', !!slideCountElement);
    
    if (!slideCountElement) {
        console.error('Slide count input element not found! Looking for #slide-count');
        alert('Slide count input not found. Please refresh the page.');
        return;
    }
    
    const slideCount = parseInt(slideCountElement.value, 10) || 6;
    console.log('Slide count value:', slideCount);
    
    // Validate input
    if (!topic) {
        alert('Please enter a presentation topic');
        return;
    }
    
    if (!templateId) {
        alert('Please select a template');
        return;
    }
    
    // Show loading indicator
    loadingIndicator.classList.remove('hidden');
    slidePreview.innerHTML = '';
    editButtonContainer.style.display = 'none';
    
    // Disable buttons during generation
    generateBtn.disabled = true;
    exportBtn.disabled = true;
    
    try {
        console.log('Sending request with slideCount:', slideCount);
        
        // Call the backend to generate content
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                template: templateId,
                topic: topic,
                slideCount: slideCount  //  ENSURE this is sent
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('Received slides:', data.slides.length, 'Expected:', slideCount);
        
        // 🔍 DEBUG: Verify slide count matches
        if (data.slides.length !== slideCount) {
            console.warn(`Slide count mismatch! Expected: ${slideCount}, Got: ${data.slides.length}`);
        }
        
        currentState = {
            slides: data.slides,
            templateId: templateId,
            topic: topic,
            currentSlideIndex: 0,
            editMode: false
        };
        
        renderCurrentSlide();
        updateEditButton();
        
        // Enable export button
        exportBtn.disabled = false;
    } catch (error) {
        console.error('Error generating slides:', error);
        alert('There was an error generating your slides. Please try again.');
        slidePreview.innerHTML = `
            <div class="placeholder-message">
                Error: Could not generate slides. Please try again.
            </div>
        `;
    } finally {
        // Hide loading indicator
        loadingIndicator.classList.add('hidden');
        generateBtn.disabled = false;
    }
}
    
    // Update the edit button outside the slide preview
    function updateEditButton() {
        if (!currentState.slides || currentState.slides.length === 0) {
            editButtonContainer.style.display = 'none';
            return;
        }
        editButtonContainer.style.display = 'flex';
    }
    
    // Export to PPTX
    async function handleExport() {
        if (!currentState.slides || currentState.slides.length === 0) {
            alert('Please generate slides first.');
            return;
        }
        
        // Exit edit mode before exporting
        if (currentState.editMode) {
            saveCurrentEdit();
        }
        
        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        exportBtn.disabled = true;
        
        try {
            // Call the backend to export PPTX
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    slides: currentState.slides,
                    template: currentState.templateId,
                    topic: currentState.topic
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            // Convert response to blob
            const blob = await response.blob();
            
            // Create a download link and trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentState.topic.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_presentation.pptx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            alert('Export completed!');
        } catch (error) {
            console.error('Error exporting to PPTX:', error);
            alert('Failed to export presentation. Please try again.');
        } finally {
            // Hide loading indicator
            loadingIndicator.classList.add('hidden');
            exportBtn.disabled = false;
        }
    }
    
    // Other required functions
    function renderCurrentSlide() {
        if (!currentState.slides || currentState.slides.length === 0) {
            return;
        }

        const currentSlide = currentState.slides[currentState.currentSlideIndex];
        slidePreview.innerHTML = window.ppgLayouts.renderPreview(
            currentSlide.layout,
            currentSlide.content,
            currentState.templateId
        );
    }
    
    function enterEditMode() {
        currentState.editMode = true;
        renderCurrentSlide();
        updateEditButton();
    }
    
    function exitEditMode() {
        currentState.editMode = false;
        renderCurrentSlide();
        updateEditButton();
    }
    
    function saveCurrentEdit() {
        const formData = window.ppgLayouts.collectFormData(
            currentState.slides[currentState.currentSlideIndex].layout
        );
        currentState.slides[currentState.currentSlideIndex].content = formData;
        exitEditMode();
    }
});