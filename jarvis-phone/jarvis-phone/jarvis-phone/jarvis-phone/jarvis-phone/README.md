# Jarvis

A private, mobile-friendly AI assistant powered by Google Gemini.

## Required environment variables

Set these in Render:

- `GEMINI_API_KEY` — your Gemini API key
- `GEMINI_MODEL` — `gemini-2.5-flash`
- `JARVIS_PASSWORD` — a strong password you create
- `FLASK_SECRET_KEY` — a long, random secret string

Never publish these secrets in GitHub or share them in chat.

## Deployment

1. Create a new Web Service on Render.
2. Connect your GitHub repository.
3. Set Root Directory to `jarvis-phone`.
4. Select Docker as the runtime.
5. Choose the Free instance.
6. Add the environment variables above.
7. Deploy.

## Current capabilities

- Password-protected AI chat
- Gemini-powered responses
- Mobile-friendly interface

External account integrations and scheduled tasks are not implemented yet.
