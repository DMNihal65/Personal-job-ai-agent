FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy source code
COPY . .

# Create a simple server file
RUN echo 'const express = require("express");\n\
const path = require("path");\n\
\n\
const app = express();\n\
const PORT = parseInt(process.env.PORT) || 8080;\n\
\n\
console.log(`Starting server on port ${PORT}`);\n\
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
            <p><strong>Backend URL:</strong> ${process.env.BACKEND_URL || "Not set"}</p>\n\
            <p><strong>Environment:</strong> ${process.env.NODE_ENV || "development"}</p>\n\
          </div>\n\
          <p>The backend API is available at: <a href="${process.env.BACKEND_URL || "#"}" target="_blank">${process.env.BACKEND_URL || "Not configured"}</a></p>\n\
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
});\n\
' > server.js

# Install express
RUN npm install express

# Make the server file executable
RUN chmod +x server.js

# Expose the port
EXPOSE 8080

# Start the server
CMD ["node", "server.js"] 