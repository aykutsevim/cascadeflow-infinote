import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'
import './App.css'

function App() {
  return (
    <div className="app-container">
      <Tldraw persistenceKey="infinote" />
    </div>
  )
}

export default App
