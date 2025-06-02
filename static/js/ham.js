// Add this JavaScript to your existing editor.js file or create a new script section

// Hamburger menu functionality
document.addEventListener('DOMContentLoaded', function() {
    // Create hamburger toggle button
    const hamburgerToggle = document.createElement('button');
    hamburgerToggle.className = 'hamburger-toggle';
    hamburgerToggle.innerHTML = '<i class="fas fa-bars"></i>';
    hamburgerToggle.setAttribute('aria-label', 'Toggle sidebar menu');
    
    // Create slides toggle button for mobile
    const slidesToggle = document.createElement('button');
    slidesToggle.className = 'slides-toggle';
    slidesToggle.innerHTML = '<i class="fas fa-images"></i>';
    slidesToggle.setAttribute('aria-label', 'Toggle slides panel');
    
    // Create overlay for mobile menu
    const sidebarOverlay = document.createElement('div');
    sidebarOverlay.className = 'sidebar-overlay';
    
    // Insert elements into DOM
    document.body.insertBefore(hamburgerToggle, document.body.firstChild);
    document.body.insertBefore(slidesToggle, document.body.firstChild);
    document.body.insertBefore(sidebarOverlay, document.body.firstChild);
    
    // Get sidebar elements
    const sidebar = document.querySelector('.sidebar');
    const rightSidebar = document.querySelector('.right-sidebar');
    
    // Hamburger toggle functionality
    hamburgerToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        sidebar.classList.toggle('open');
        sidebarOverlay.classList.toggle('show');
        
        // Close right sidebar if open
        rightSidebar.classList.remove('open');
        
        // Update hamburger icon
        const icon = hamburgerToggle.querySelector('i');
        if (sidebar.classList.contains('open')) {
            icon.className = 'fas fa-times';
        } else {
            icon.className = 'fas fa-bars';
        }
    });
    
    // Slides toggle functionality
    slidesToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        rightSidebar.classList.toggle('open');
        sidebarOverlay.classList.toggle('show');
        
        // Close left sidebar if open
        sidebar.classList.remove('open');
        
        // Update slides icon
        const icon = slidesToggle.querySelector('i');
        if (rightSidebar.classList.contains('open')) {
            icon.className = 'fas fa-times';
        } else {
            icon.className = 'fas fa-images';
        }
        
        // Update hamburger icon
        const hamburgerIcon = hamburgerToggle.querySelector('i');
        hamburgerIcon.className = 'fas fa-bars';
    });
    
    // Overlay click to close menus
    sidebarOverlay.addEventListener('click', function() {
        sidebar.classList.remove('open');
        rightSidebar.classList.remove('open');
        sidebarOverlay.classList.remove('show');
        
        // Reset icons
        hamburgerToggle.querySelector('i').className = 'fas fa-bars';
        slidesToggle.querySelector('i').className = 'fas fa-images';
    });
    
    // Close menus when clicking outside
    document.addEventListener('click', function(e) {
        if (!sidebar.contains(e.target) && 
            !rightSidebar.contains(e.target) && 
            !hamburgerToggle.contains(e.target) && 
            !slidesToggle.contains(e.target)) {
            
            sidebar.classList.remove('open');
            rightSidebar.classList.remove('open');
            sidebarOverlay.classList.remove('show');
            
            // Reset icons
            hamburgerToggle.querySelector('i').className = 'fas fa-bars';
            slidesToggle.querySelector('i').className = 'fas fa-images';
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const width = window.innerWidth;
        
        // Auto-close mobile menus on desktop
        if (width > 1024) {
            sidebar.classList.remove('open');
            rightSidebar.classList.remove('open');
            sidebarOverlay.classList.remove('show');
            
            // Reset icons
            hamburgerToggle.querySelector('i').className = 'fas fa-bars';
            slidesToggle.querySelector('i').className = 'fas fa-images';
        }
    });
    
    // Prevent menu content clicks from closing the menu
    sidebar.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    rightSidebar.addEventListener('click', function(e) {
        e.stopPropagation();
    });
});

// Optional: Add smooth scroll behavior for better UX
function smoothScrollToPreview() {
    const previewContainer = document.querySelector('.preview-container');
    if (previewContainer) {
        previewContainer.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
    }
}

// Call this function when navigation occurs or preview updates
// You can integrate this with your existing slide navigation code