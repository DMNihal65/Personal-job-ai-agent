const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

// Simple middleware to log requests
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Basic route
app.get('/', (req, res) => {
  res.send('Hello from Cloud Run! The server is working correctly.');
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
  console.log(`Environment variables: ${JSON.stringify(process.env, null, 2)}`);
}); 