FROM node:20-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Create a simple server to serve the static files
RUN echo 'const express = require("express");\n\
const path = require("path");\n\
const fs = require("fs");\n\
\n\
const app = express();\n\
const PORT = process.env.PORT || 8080;\n\
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";\n\
\n\
// Log environment variables\n\
console.log("Starting server with:");\n\
console.log(`PORT: ${PORT}`);\n\
console.log(`BACKEND_URL: ${BACKEND_URL}`);\n\
\n\
// Replace BACKEND_URL in the built files\n\
const replaceBackendUrl = () => {\n\
  const indexPath = path.join(__dirname, "dist", "index.html");\n\
  let content = fs.readFileSync(indexPath, "utf8");\n\
  content = content.replace(/BACKEND_URL_PLACEHOLDER/g, BACKEND_URL);\n\
  fs.writeFileSync(indexPath, content);\n\
  console.log("Replaced backend URL in index.html");\n\
};\n\
\n\
// Replace the backend URL before starting the server\n\
replaceBackendUrl();\n\
\n\
// Serve static files\n\
app.use(express.static(path.join(__dirname, "dist")));\n\
\n\
// Handle API requests\n\
app.use("/api", (req, res) => {\n\
  res.redirect(`${BACKEND_URL}${req.url}`);\n\
});\n\
\n\
// For any other request, serve the React app\n\
app.get("*", (req, res) => {\n\
  res.sendFile(path.join(__dirname, "dist", "index.html"));\n\
});\n\
\n\
// Start the server\n\
app.listen(PORT, () => {\n\
  console.log(`Server running on port ${PORT}`);\n\
});' > server.js

# Install express for the server
RUN npm install express

# Final image
FROM node:20-alpine

WORKDIR /app

# Copy built app and server
COPY --from=build /app/dist ./dist
COPY --from=build /app/server.js .
COPY --from=build /app/node_modules ./node_modules

# Expose the port
EXPOSE 8080

# Start the server
CMD ["node", "server.js"] 