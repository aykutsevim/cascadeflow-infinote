import { useState, useCallback } from 'react'
import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'
import './App.css'
import PhotoCapture from './components/PhotoCapture'

function App() {
  const [editor, setEditor] = useState(null)

  const handleMount = useCallback((editorInstance) => {
    setEditor(editorInstance)
  }, [])

  return (
    <div className="app-container">
      <Tldraw persistenceKey="infinote" onMount={handleMount} />
      <PhotoCapture editor={editor} />
    </div>
  )
}

export default App
