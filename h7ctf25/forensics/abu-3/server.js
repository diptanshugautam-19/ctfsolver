const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Correct answers (stored securely on server)
const ANSWERS = {
  q9: '45a7ef83238f5244738bb5e7e3dd6299',
  q10: '4',
  q11: 'xmr-eu1.nanopool.org',
  q12: '46V5WXwS3gXfsgR7fgXeGP4KAXtQTXJfkicBoRSHXwGbhVzj1JXZRJRhbMrvhxvXvgbJuyV3GGWzD6JvVMuQwAXxLZmTWkb',
  q13: '3',
  q14: 'stratum',
  q15: '44MtPEErzyDNHfggtup49m4zwGm7zjYp5jWKWRc3go6LN5fxetsHtVhdEetL9jhZedNAwG7YGLpR1azK5Ch69cdGPgVj5wA',
  q16: '2022-03-19'
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
  if (question === 'q9') {
    // Case-insensitive for MD5 hash
    isCorrect = answer?.toLowerCase() === correctAnswer.toLowerCase();
  } else if (question === 'q14') {
    // Case-insensitive for protocol, accept with or without +tcp
    const normalized = answer?.toLowerCase().replace(/\+tcp$/, '');
    isCorrect = normalized === 'stratum';
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
    
    if (key === 'q9') {
      // Case-insensitive for MD5 hash
      isCorrect = userAnswer?.toLowerCase() === correctAnswer.toLowerCase();
    } else if (key === 'q14') {
      // Case-insensitive for protocol, accept with or without +tcp
      const normalized = userAnswer?.toLowerCase().replace(/\+tcp$/, '');
      isCorrect = normalized === 'stratum';
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
  res.json({ status: 'ok', challenge: 'KGF Part 2' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`KGF Part 2 server listening on port ${PORT}`);
});
