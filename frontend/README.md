# Infinote

A React app with tldraw for drawing and note-taking, with automatic local storage persistence.

## Features

- Full-featured drawing canvas powered by tldraw
- Built-in note-taking capabilities (use the text tool from the toolbar)
- Automatic persistence - your work is saved automatically
- Persistent state - your drawings and notes are restored when you reload the page
- Clean, fullscreen interface

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser at `http://localhost:5173/`

## How to Use

- Use the toolbar on the left to select different tools (draw, text, shapes, etc.)
- Click the text tool to create notes anywhere on the canvas
- Your work is automatically saved to browser storage
- Refresh the page anytime - your work will be restored

## Technologies

- React + Vite
- tldraw - infinite canvas drawing library
- localStorage for persistence

## Storage

All data is stored locally in your browser using IndexedDB (tldraw's built-in persistence with key `infinote`). To clear your workspace, open browser DevTools > Application > IndexedDB > tldraw and delete the database, or use the tldraw menu > Preferences > Reset.
