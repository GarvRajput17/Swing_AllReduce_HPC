/* global monogatari */

// Define the messages used in the game
monogatari.action('message').messages({
    'Help': {
        title: 'Interactive Financial Education',
        subtitle: 'How to Play',
        body: `
            <p>Welcome to your personalized financial education experience!</p>
            <p>Learn about ${localStorage.getItem('currentConcept') || 'finance'} through an engaging story.</p>
            <p>Controls:</p>
            <ul>
                <li>Click or press Space/Enter to advance</li>
                <li>Use the menu to save/load your progress</li>
                <li>Press H for help anytime</li>
            </ul>
        `
    }
});

// Define the notifications
monogatari.action('notification').notifications({
    'Welcome': {
        title: 'Welcome to Your Financial Story',
        body: 'Learn financial concepts through interactive storytelling!',
        icon: story => story.generated_images.cover || '/output/images/financial_comic_8685.png'
    }
});

// Define the credits
monogatari.configuration('credits', {
    'Financial Education Story': {
        'Development': 'AppXcess Team',
        'Story Generation': 'Powered by Google Gemini',
        'Visual Novel Engine': 'Monogatari'
    }
});

// Configure game settings
monogatari.configuration('keys', {
    'Enter': {
        'name': 'Enter',
        'description': 'Continue Story',
        'action': 'next'
    },
    'Space': {
        'name': 'Space',
        'description': 'Continue Story',
        'action': 'next'
    },
    'H': {
        'name': 'H',
        'description': 'Show Help',
        'action': 'open-screen',
        'parameters': ['help']
    }
});

// Animation settings
monogatari.configuration('TypeAnimation', {
    'Speed': 35,
    'enabled': true
});

// Theme configuration
monogatari.configuration('theme', {
    'primary': '#2196F3',
    'secondary': '#607D8B',
    'text': '#ffffff'
});
