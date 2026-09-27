// Update character count hints and validate individual answers
document.querySelectorAll('input[type="text"]').forEach(input => {
    const hint = input.nextElementSibling;
    const expectedLength = input.dataset.length;
    
    // Initialize hint
    updateHint(input, hint, expectedLength);
    
    // Update on input
    input.addEventListener('input', () => {
        updateHint(input, hint, expectedLength);
    });
    
    // Validate answer on blur (when user leaves the field)
    input.addEventListener('blur', async () => {
        if (input.value.trim().length > 0) {
            await checkIndividualAnswer(input.name, input.value.trim());
        }
    });
});

function updateHint(input, hint, expectedLength) {
    const currentLength = input.value.length;
    if (currentLength === 0) {
        hint.textContent = `Expected length: ${expectedLength} characters`;
    } else {
        hint.textContent = `${currentLength} / ${expectedLength} characters`;
        
        if (currentLength === parseInt(expectedLength)) {
            hint.style.color = '#2ecc71';
        } else {
            hint.style.color = '#666';
        }
    }
}

// Check individual answer
async function checkIndividualAnswer(question, answer) {
    try {
        const response = await fetch('/api/check-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question, answer })
        });
        
        const data = await response.json();
        const input = document.getElementById(question);
        const questionDiv = input.closest('.question');
        
        // Remove previous validation states
        questionDiv.classList.remove('correct', 'incorrect');
        
        // Add new validation state
        if (data.valid) {
            questionDiv.classList.add('correct');
            input.style.borderColor = '#2ecc71';
        } else {
            questionDiv.classList.add('incorrect');
            input.style.borderColor = '#e74c3c';
        }
        
    } catch (error) {
        console.error('Error checking answer:', error);
    }
}

// Handle form submission
document.getElementById('challengeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const resultDiv = document.getElementById('result');
    const flagDiv = document.getElementById('flag');
    
    // Disable button during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Validating...';
    
    // Collect answers
    const answers = {};
    const inputs = document.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        answers[input.name] = input.value.trim();
    });
    
    try {
        // Send to server for validation
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(answers)
        });
        
        const data = await response.json();
        
        // Show results
        resultDiv.classList.remove('hidden', 'success', 'error');
        flagDiv.classList.add('hidden');
        
        // Mark correct/incorrect questions
        document.querySelectorAll('.question').forEach(q => {
            q.classList.remove('correct', 'incorrect');
        });
        
        for (const [key, isCorrect] of Object.entries(data.results)) {
            const input = document.getElementById(key);
            const question = input.closest('.question');
            question.classList.add(isCorrect ? 'correct' : 'incorrect');
        }
        
        if (data.success) {
            resultDiv.classList.add('success');
            resultDiv.textContent = 'All answers correct! Here is your flag:';
            
            flagDiv.classList.remove('hidden');
            flagDiv.innerHTML = `
                <h3>FLAG</h3>
                <code>${data.flag}</code>
            `;
        } else {
            resultDiv.classList.add('error');
            const incorrectCount = Object.values(data.results).filter(r => !r).length;
            resultDiv.textContent = `${incorrectCount} answer(s) incorrect. Check the highlighted questions.`;
        }
        
    } catch (error) {
        resultDiv.classList.remove('hidden');
        resultDiv.classList.add('error');
        resultDiv.textContent = 'Error validating answers. Please try again.';
        console.error('Validation error:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit All Answers';
    }
});
