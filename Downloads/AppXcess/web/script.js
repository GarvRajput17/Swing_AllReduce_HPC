/* global monogatari */

monogatari.ready(function () {
    async function loadStory() {
        try {
            // First try to get latest story if no ID in storage
            const storyId = localStorage.getItem('currentStoryId');
            const endpoint = storyId ? `/api/story/${storyId}` : '/api/latest-story';
            
            const response = await fetch(endpoint);
            const data = await response.json();
            
            if (data.success) {
                // Store the ID for future reference
                localStorage.setItem('currentStoryId', data.story.story_id);
                return data.story.frontend_format;
            } else {
                console.error('Failed to load story:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Error loading story:', error);
            return null;
        }
    }
    
    // Convert the story data to Monogatari script format
    function convertStoryToScript(story) {
        if (!story) {
            return {
                'Start': [
                    'show scene #000000',
                    'centered Error loading story. Please try again.',
                    'end'
                ]
            };
        }
        
        const script = {
            'Start': [
                'show scene #000000',
                `centered ${story.plot.title}`,
                `centered Location: ${story.plot.location}`,
                'wait 1000'
            ]
        };
        
        // Add each dialogue scene
        story.dialogue_scenes.forEach((scene, index) => {
            const sceneName = `Scene${index + 1}`;
            script[sceneName] = [];
            
            // Set background
            if (scene.background_image) {
                script[sceneName].push(`show scene ${scene.background_image}`);
            }
            
            // Show character
            if (scene.character_image) {
                script[sceneName].push(`show character ${scene.dialogue.character.toLowerCase()} ${scene.character_image}`);
            }
            
            // Add dialogue
            script[sceneName].push(`${scene.dialogue.character.toLowerCase()} ${scene.dialogue.text}`);
            
            // Link to next scene or ending
            if (index < story.dialogue_scenes.length - 1) {
                script[sceneName].push(`jump Scene${index + 2}`);
            } else {
                script[sceneName].push('jump Ending');
            }
        });
        
        // Add ending scene
        script['Ending'] = [
            'show scene #000000',
            'centered The End',
            {
                'Choice': {
                    'Generate Another Story': {
                        'Text': 'Generate Another Story',
                        'Do': function() {
                            window.location.href = '/';
                            return 'wait';
                        }
                    }
                }
            },
            'end'
        ];
        
        return script;
    }
    
    // Load and set up the story
    loadStory().then(story => {
        const script = convertStoryToScript(story);
        monogatari.script(script);
        
        // Start from the beginning
        monogatari.run();
    });
});
