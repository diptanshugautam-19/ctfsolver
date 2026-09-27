const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Correct answers (stored securely on server)
const ANSWERS = {
  q1: '80.64.16.241',
  q2: 'http://80.64.16.241/d.sh',
  q3: '4',
  q4: '2025-07-09 17:12:05',
  q5: 'XMR',
  q6: '711',
  q7: '99.0.4844.51',
  q8: 'firewire'
};

// Individual answer validation endpoint
app.post('/api/check-answer', (req, res) => {
  const { question, answer } = req.body;
  
  if (!question || !ANSWERS[question]) {
    return res.json({ valid: false, error: 'Invalid question' });
  }
  
  const correctAnswer = ANSWERS[question];
  let isCorrect = false;
  
  // Normalize answers for comparison
  if (question === 'q5') {
    // Case-insensitive for crypto ticker
    isCorrect = answer?.toUpperCase() === correctAnswer.toUpperCase();
  } else {
    // Exact match for others
    isCorrect = answer === correctAnswer;
  }
  
  res.json({ 
    valid: isCorrect,
    question: question
  });
});

// Full form validation endpoint
app.post('/api/validate', (req, res) => {
  const userAnswers = req.body;
  const results = {};
  let allCorrect = true;

  // Check each answer
  for (const [key, correctAnswer] of Object.entries(ANSWERS)) {
    const userAnswer = userAnswers[key];
    
    // Normalize answers for comparison
    let isCorrect = false;
    
    if (key === 'q5') {
      // Case-insensitive for crypto ticker
      isCorrect = userAnswer?.toUpperCase() === correctAnswer.toUpperCase();
    } else {
      // Exact match for others
      isCorrect = userAnswer === correctAnswer;
    }
    
    results[key] = isCorrect;
    if (!isCorrect) allCorrect = false;
  }

  // If all correct, send flag
  if (allCorrect) {
    const flag = process.env.FLAG || 'H7CTF{test_flag_not_set}';
    res.json({
      success: true,
      message: 'All answers correct!',
      flag: flag,
      results: results
    });
  } else {
    res.json({
      success: false,
      message: 'Some answers are incorrect. Keep trying!',
      results: results
    });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', challenge: 'KGF Part 1' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`KGF Part 1 server listening on port ${PORT}`);
});
