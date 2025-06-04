// app.js - Main application logic for the PowerPoint generator with editing functionality

document.addEventListener('DOMContentLoaded', function () {
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

    async function generateWithOutline(inputMethod) {
        // Stage 1: Generate outline
        showLoadingWithMessage("Creating presentation outline...");

        const outlineData = {
            topic: getTopicFromCurrentMethod(),
            slideCount: parseInt(document.getElementById('slide-count').value) || 5,
            inputMethod: inputMethod
        };

        if (inputMethod === 'text') {
            outlineData.textContent = window.inputMethodsHandler.getTextContent();
        }

        console.log('Generating outline with data:', outlineData);

        const outlineResponse = await fetch('/api/generate-outline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(outlineData)
        });

        if (!outlineResponse.ok) {
            const errorData = await outlineResponse.json().catch(() => ({}));
            throw new Error(errorData.error || `Outline generation failed: ${outlineResponse.status}`);
        }

        const outlineResult = await outlineResponse.json();
        console.log('Outline generated:', outlineResult);


        const approvedOutline = outlineResult.outline; // Auto-approve for now

        // Stage 2: Generate slides from outline
        showLoadingWithMessage("Generating slides with context and flow...");

        const slidesResponse = await fetch('/api/generate-from-outline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                outline: approvedOutline,
                template: window.selectedTemplateId
            })
        });

        if (!slidesResponse.ok) {
            const errorData = await slidesResponse.json().catch(() => ({}));
            throw new Error(errorData.error || `Slide generation failed: ${slidesResponse.status}`);
        }

        const slidesResult = await slidesResponse.json();
        console.log('Slides generated from outline:', slidesResult);

        return {
            slides: slidesResult.slides,
            outline: slidesResult.outline,
            generation_method: 'outline-based'
        };
    }

    function showLoadingWithMessage(message) {
        const loadingIndicator = document.getElementById('loading');
        const loadingText = loadingIndicator.querySelector('p');

        if (loadingText) {
            loadingText.textContent = message;
        }

        loadingIndicator.classList.remove('hidden');
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