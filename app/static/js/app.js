console.log('App JS loaded');


// Force dark mode BEFORE any page load - THIS IS THE KEY
(function() {
    const stored = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = stored === 'dark' || (!stored && prefersDark);
    
    if (isDark) {
        document.documentElement.classList.add('dark-mode');
        document.documentElement.classList.remove('light-mode');
        document.documentElement.style.backgroundColor = '#0f0f1a';
        document.body.style.backgroundColor = '#0f0f1a';
    }
    
    // Intercept all fetch/xhr to ensure no flash
    const originalFetch = window.fetch;
    window.fetch = function() {
        // Preserve theme before network request
        const theme = document.documentElement.classList.contains('dark-mode') ? 'dark' : 'light';
        sessionStorage.setItem('preFloodTheme', theme);
        return originalFetch.apply(this, arguments);
    };
})();

// Listen for page navigation
window.addEventListener('pageshow', function() {
    const theme = sessionStorage.getItem('preFloodTheme') || localStorage.getItem('theme');
    if (theme === 'dark') {
        document.documentElement.classList.add('dark-mode');
        document.documentElement.classList.remove('light-mode');
        document.documentElement.style.backgroundColor = '#0f0f1a';
        document.body.style.backgroundColor = '#0f0f1a';
    }
    sessionStorage.removeItem('preFloodTheme');
});
// Dark Mode Toggle Functionality
(function() {
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.documentElement.classList.add('dark');
        updateDarkModeIcon(true);
    } else {
        document.documentElement.classList.remove('dark');
        updateDarkModeIcon(false);
    }
    
    // Function to update the icon based on dark mode state
    function updateDarkModeIcon(isDark) {
        const icon = document.getElementById('darkModeIcon');
        if (icon) {
            if (isDark) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        }
    }
    
    // Function to toggle dark mode
    function toggleDarkMode() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateDarkModeIcon(isDark);
        
        // Dispatch event for other components to react
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { isDark } }));
    }
    
    // Add click event listener to dark mode toggle button
    const toggleButton = document.getElementById('darkModeToggle');
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleDarkMode);
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                document.documentElement.classList.add('dark');
                updateDarkModeIcon(true);
            } else {
                document.documentElement.classList.remove('dark');
                updateDarkModeIcon(false);
            }
        }
    });
})();

