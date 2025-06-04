// Updated create.js for new flow
document.addEventListener('DOMContentLoaded', function() {
    const methodCards = document.querySelectorAll('.method-card');
    
    methodCards.forEach(card => {
        card.addEventListener('click', function() {
            const method = this.dataset.method;
            handleMethodSelection(method);
        });
        
        // Add hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key >= '1' && e.key <= '3') {
            const index = parseInt(e.key) - 1;
            const cards = Array.from(methodCards);
            if (cards[index]) {
                cards[index].click();
            }
        }
    });
});

function handleMethodSelection(method) {
    const card = document.querySelector(`[data-method="${method}"]`);
    
    // Add loading state
    card.classList.add('loading');
    
    // Add success animation
    setTimeout(() => {
        card.style.transform = 'scale(0.95)';
        setTimeout(() => {
            // Navigate to generation page with method parameter
            window.location.href = `/create/generate?method=${method}`;
        }, 200);
    }, 300);
}

// Add some delightful animations on load
function animateOnLoad() {
    const cards = document.querySelectorAll('.method-card');
    const hero = document.querySelector('.create-hero');
    
    // Animate hero
    if (hero) {
        hero.style.opacity = '0';
        hero.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            hero.style.transition = 'all 0.8s ease';
            hero.style.opacity = '1';
            hero.style.transform = 'translateY(0)';
        }, 100);
    }
    
    // Animate cards with stagger
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 300 + (index * 150));
    });
}

// Run animations on load
document.addEventListener('DOMContentLoaded', animateOnLoad);