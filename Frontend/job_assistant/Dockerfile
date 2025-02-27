FROM node:20-alpine

WORKDIR /app

# Create package.json
RUN echo '{\n\
  "name": "resume-agent-frontend",\n\
  "version": "1.0.0",\n\
  "description": "Simple frontend for Resume Agent",\n\
  "main": "server.js",\n\
  "scripts": {\n\
    "start": "node server.js"\n\
  },\n\
  "dependencies": {\n\
    "express": "^4.18.2"\n\
  }\n\
}' > package.json

# Install dependencies
RUN npm install

# Create server.js
RUN echo 'const express = require("express");\n\
const path = require("path");\n\
\n\
const app = express();\n\
const PORT = parseInt(process.env.PORT) || 8080;\n\
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";\n\
\n\
console.log(`Starting server on port ${PORT}`);\n\
console.log(`Backend URL: ${BACKEND_URL}`);\n\
\n\
// Basic route for testing\n\
app.get("/", (req, res) => {\n\
  res.send(`\n\
    <html>\n\
      <head>\n\
        <title>Resume Agent Frontend</title>\n\
        <style>\n\
          body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }\n\
          h1 { color: #333; }\n\
          .container { border: 1px solid #ddd; padding: 20px; border-radius: 5px; }\n\
          .info { background-color: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }\n\
        </style>\n\
      </head>\n\
      <body>\n\
        <h1>Resume Agent Frontend</h1>\n\
        <div class="container">\n\
          <p>This is a simple test page for the Resume Agent Frontend.</p>\n\
          <div class="info">\n\
            <p><strong>Port:</strong> ${PORT}</p>\n\
            <p><strong>Backend URL:</strong> ${BACKEND_URL || "Not set"}</p>\n\
          </div>\n\
          <p>The backend API is available at: <a href="${BACKEND_URL || "#"}" target="_blank">${BACKEND_URL || "Not configured"}</a></p>\n\
        </div>\n\
      </body>\n\
    </html>\n\
  `);\n\
});\n\
\n\
// Health check endpoint\n\
app.get("/health", (req, res) => {\n\
  res.status(200).send("OK");\n\
});\n\
\n\
// Start the server with proper error handling\n\
const server = app.listen(PORT, "0.0.0.0", () => {\n\
  console.log(`Server running at http://0.0.0.0:${PORT}/`);\n\
});\n\
\n\
// Handle errors\n\
server.on("error", (err) => {\n\
  console.error("Server error:", err);\n\
});\n\
\n\
// Handle graceful shutdown\n\
process.on("SIGTERM", () => {\n\
  console.log("SIGTERM received, shutting down...");\n\
  server.close(() => {\n\
    console.log("Server closed");\n\
  });\n\
});' > server.js

# Expose port 8080
EXPOSE 8080

# Start the server
CMD ["node", "server.js"] 