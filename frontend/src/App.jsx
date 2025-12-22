import { useState, useCallback, useMemo } from 'react'
import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'
import './App.css'
import PhotoCapture from './components/PhotoCapture'
import { TaskCardShapeUtil } from './shapes/TaskCardShape'

// Custom shape utilities for the editor
const customShapeUtils = [TaskCardShapeUtil]

function App() {
  const [editor, setEditor] = useState(null)

  const handleMount = useCallback((editorInstance) => {
    setEditor(editorInstance)
  }, [])

  return (
    <div className="app-container">
      <Tldraw
        persistenceKey="infinote"
        onMount={handleMount}
        shapeUtils={customShapeUtils}
      />
      <PhotoCapture editor={editor} />
    </div>
  )
}

export default App
