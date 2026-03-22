# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (React)
- `npm start` - Start React development server on http://localhost:3000
- `npm test` - Run test runner in watch mode
- `npm run build` - Build production bundle

### Backend (FastAPI)
- Backend runs on Python 3.11.9 using FastAPI
- Uses PostgreSQL database named 'bread_makes'
- Development server likely runs with `uvicorn` or `fastapi dev`

### Database
- PostgreSQL 15 is required (`brew install postgresql@15`)
- Database schema files are in `/database/` directory
- Main tables: `account_makes`, `dough_makes`

## Architecture Overview

This is a bread making tracking application with:

**Frontend**: React + TypeScript app using:
- Material-UI for components (DatePicker, TimePicker, Modal, etc.)
- Tailwind CSS for styling
- Wouter for routing
- dayjs for date handling
- Custom navigation context and hooks

**Backend**: FastAPI Python service with:
- PostgreSQL database integration via custom `DBConnector` class
- Pydantic models for request/response validation
- OAuth2 authentication scheme (token-based)
- CORS enabled for development
- Main models: `DoughMake`, `AccountMake`, `SimpleMake`

**Key Features**:
- Track bread making processes with timestamps
- Temperature management for different stages
- Stretch and fold tracking
- Multiple bread types (demi-baguette, hoagie, ube, team)
- User account management

**API Testing**: Bruno collection in `/Bread App/` for API endpoint testing

The application tracks the bread making process from dough creation through baking, with detailed temperature and timing controls.