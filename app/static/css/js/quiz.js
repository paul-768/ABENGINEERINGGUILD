// Quiz-specific JavaScript - NO POPUP VERSION
document.addEventListener('DOMContentLoaded', function() {
    initializeQuiz();
});

function initializeQuiz() {
    // Quiz timer functionality
    const timerElement = document.getElementById('time-remaining');
    if (timerElement) {
        startQuizTimer();
    }

    // Quiz form submission handling
    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
        quizForm.addEventListener('submit', handleQuizSubmission);
        
        // Auto-save answer when selected
        const answerInputs = quizForm.querySelectorAll('input[name="answer"]');
        answerInputs.forEach(input => {
            input.addEventListener('change', saveQuizProgress);
        });
    }

    // Initialize any saved answers
    loadSavedAnswers();
    
    // Set up periodic auto-saving
    setInterval(saveQuizProgress, 30000);
}

function startQuizTimer() {
    const timerElement = document.getElementById('time-remaining');
    const timeTakenInput = document.getElementById('time-taken');
    const formElement = document.getElementById('quiz-form');
    
    if (!timerElement) return;
    
    let seconds = parseInt(timerElement.textContent);
    const initialSeconds = seconds;
    
    const countdown = setInterval(function() {
        seconds--;
        timerElement.textContent = seconds;
        
        // Update hidden time taken input
        if (timeTakenInput) {
            timeTakenInput.value = initialSeconds - seconds;
        }
        
        // Visual warning when time is running low
        if (seconds <= 10) {
            timerElement.parentElement.classList.add('timer-warning');
            timerElement.classList.add('animate-pulse');
        }
        
        // Critical time warning
        if (seconds <= 5) {
            timerElement.parentElement.classList.add('timer-critical');
        }
        
        // Auto-submit when time runs out - NO POPUP
        if (seconds <= 0) {
            clearInterval(countdown);
            if (formElement) {
                // Direct submit without any popup notification
                formElement.submit();
            }
        }
    }, 1000);
    
    // Store timer reference for cleanup
    window.quizTimer = countdown;
}

function handleQuizSubmission(e) {
    const form = e.target;
    const answer = form.querySelector('input[name="answer"]:checked');
    const questionNum = parseInt(form.querySelector('input[name="question_num"]').value);
    const totalQuestions = parseInt(form.querySelector('input[name="total_questions"]')?.value || 0);
    
    // For questions beyond the first, require an answer
    if (!answer && questionNum > 1) {
        e.preventDefault();
        // Show inline error message instead of toast
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.classList.remove('hidden');
            errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return false;
    }
    
    // Show loading indicator
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
        `;
    }
    
    // Save progress before submitting
    saveQuizProgress();
}

function saveQuizProgress() {
    const form = document.getElementById('quiz-form');
    if (!form) return;
    
    const questionId = form.querySelector('input[name="question_id"]').value;
    const answer = form.querySelector('input[name="answer"]:checked');
    
    if (answer) {
        // Store in sessionStorage
        const answers = JSON.parse(sessionStorage.getItem('quiz_answers') || '{}');
        answers[questionId] = answer.value;
        sessionStorage.setItem('quiz_answers', JSON.stringify(answers));
        
        // Visual indicator that answer is saved
        const indicator = document.getElementById('save-indicator') || createSaveIndicator();
        indicator.textContent = 'Answer saved';
        indicator.classList.remove('hidden');
        
        setTimeout(() => {
            indicator.classList.add('hidden');
        }, 2000);
    }
}

function loadSavedAnswers() {
    const answers = JSON.parse(sessionStorage.getItem('quiz_answers') || '{}');
    const form = document.getElementById('quiz-form');
    
    if (!form) return;
    
    const questionId = form.querySelector('input[name="question_id"]').value;
    const savedAnswer = answers[questionId];
    
    if (savedAnswer) {
        const answerInput = form.querySelector(`input[name="answer"][value="${savedAnswer}"]`);
        if (answerInput) {
            answerInput.checked = true;
        }
    }
}

function createSaveIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'save-indicator';
    indicator.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg hidden z-50';
    document.body.appendChild(indicator);
    return indicator;
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    // Only handle keyboard navigation if not in an input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    const form = document.getElementById('quiz-form');
    if (!form) return;
    
    // Number keys 1-4 for answer selection
    if (e.key >= '1' && e.key <= '4') {
        const answerIndex = parseInt(e.key) - 1;
        const answerInputs = form.querySelectorAll('input[name="answer"]');
        if (answerInputs[answerIndex]) {
            answerInputs[answerIndex].checked = true;
            saveQuizProgress();
        }
    }
    
    // Enter to submit
    if (e.key === 'Enter') {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.click();
        }
    }
    
    // N for next, P for previous (if available)
    if (e.key === 'n' || e.key === 'N') {
        const nextButton = document.querySelector('.next-question');
        if (nextButton) nextButton.click();
    }
    
    if (e.key === 'p' || e.key === 'P') {
        const prevButton = document.querySelector('.prev-question');
        if (prevButton) prevButton.click();
    }
});

// Clean up when leaving the page
window.addEventListener('beforeunload', function() {
    if (window.quizTimer) {
        clearInterval(window.quizTimer);
    }
    
    // Optional: Confirm before leaving if answers are unsaved
    const form = document.getElementById('quiz-form');
    if (form) {
        const answer = form.querySelector('input[name="answer"]:checked');
        if (!answer) {
            return 'You have not selected an answer. Are you sure you want to leave?';
        }
    }
});

// Export functions for potential use elsewhere
window.QuizUtils = {
    saveProgress: saveQuizProgress
};