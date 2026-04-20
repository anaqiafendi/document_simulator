import { BrowserRouter, Routes, Route } from 'react-router-dom'
import NavBar from './components/NavBar'

// Existing Synthetic Generator (root route)
import SyntheticGenerator from './SyntheticGenerator'

// New pages
import AugmentationLab from './pages/AugmentationLab'
import OcrEngine from './pages/OcrEngine'
import BatchProcessing from './pages/BatchProcessing'
import Evaluation from './pages/Evaluation'
import RlTraining from './pages/RlTraining'
import SchemaExtraction from './pages/SchemaExtraction'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ fontFamily: 'system-ui, sans-serif', minHeight: '100vh', background: '#f8f8fb' }}>
        <NavBar />
        <Routes>
          <Route path="/" element={<SyntheticGenerator />} />
          <Route path="/augmentation" element={<AugmentationLab />} />
          <Route path="/ocr" element={<OcrEngine />} />
          <Route path="/batch" element={<BatchProcessing />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/rl" element={<RlTraining />} />
          <Route path="/schema-extraction" element={<SchemaExtraction />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
