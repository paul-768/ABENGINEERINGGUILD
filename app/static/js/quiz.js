// Quiz-specific JavaScript - EXTREME CLEAN VERSION
console.log('Quiz JS loaded - EXTREME VERSION');

// Kill all functions at module level
window.showToast = null;
window.createToast = null;
window.notify = null;
window.alert = function() { return true; };

document.addEventListener('DOMContentLoaded', function() {
    initializeQuiz();
});

function initializeQuiz() {
    const timerElement = document.getElementById('time-remaining');
    if (timerElement) {
        startQuizTimer();
    }

    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
        quizForm.addEventListener('submit', handleQuizSubmission);
        
        const answerInputs = quizForm.querySelectorAll('input[name="answer"]');
        answerInputs.forEach(input => {
            input.addEventListener('change', saveQuizProgress);
        });
    }

    loadSavedAnswers();
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
        if (timerElement) timerElement.textContent = seconds;
        if (timeTakenInput) timeTakenInput.value = initialSeconds - seconds;
        
        if (seconds <= 0) {
            clearInterval(countdown);
            if (formElement) {
                // DIRECT SUBMIT - NO MESSAGES
                formElement.submit();
            }
        }
    }, 1000);
    
    window.quizTimer = countdown;
}

function handleQuizSubmission(e) {
    const form = e.target;
    const answer = form.querySelector('input[name="answer"]:checked');
    const questionNum = parseInt(form.querySelector('input[name="question_num"]').value);
    
    if (!answer && questionNum > 1) {
        e.preventDefault();
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.classList.remove('hidden');
        }
        return false;
    }
    
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing...`;
    }
    
    saveQuizProgress();
}

function saveQuizProgress() {
    const form = document.getElementById('quiz-form');
    if (!form) return;
    
    const questionId = form.querySelector('input[name="question_id"]').value;
    const answer = form.querySelector('input[name="answer"]:checked');
    
    if (answer) {
        const answers = JSON.parse(sessionStorage.getItem('quiz_answers') || '{}');
        answers[questionId] = answer.value;
        sessionStorage.setItem('quiz_answers', JSON.stringify(answers));
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