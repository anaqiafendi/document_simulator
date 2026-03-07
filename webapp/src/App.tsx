import { useState } from 'react'
import type { TemplateInfo, ZoneConfig, RespondentConfig, PreviewSample, JobStatus } from './types'
import { uploadTemplate, fetchPreviews, startGenerate, getJobStatus, downloadUrl } from './api/client'

const DEFAULT_RESPONDENT: RespondentConfig = {
  respondent_id: 'default',
  display_name: 'Default',
  field_types: [{
    field_type_id: 'standard',
    display_name: 'Standard',
    font_family: 'sans-serif',
    font_size_range: [10, 14],
    font_color: '#000000',
    bold: false,
    italic: false,
    fill_style: 'typed',
    jitter_x: 0.05,
    jitter_y: 0.02,
    baseline_wander: 0.0,
    char_spacing_jitter: 0.0,
  }],
}

export default function App() {
  const [templateInfo, setTemplateInfo] = useState<TemplateInfo | null>(null)
  const [zones, setZones] = useState<ZoneConfig[]>([])
  const [respondents, setRespondents] = useState<RespondentConfig[]>([DEFAULT_RESPONDENT])
  const [previews, setPreviews] = useState<PreviewSample[]>([])
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generateN, setGenerateN] = useState(10)
  const [outputDir, setOutputDir] = useState('/tmp/synthetic_output')
  const [downloadJobId, setDownloadJobId] = useState<string | null>(null)

  // zones is declared but used through setZones; include in build to avoid TS unused-var error
  void zones

  const buildSynthesisConfig = () => ({
    respondents,
    zones,
    generator: {
      image_width: templateInfo?.width_px ?? 800,
      image_height: templateInfo?.height_px ?? 1000,
      output_dir: outputDir,
      seed: 42,
      n: generateN,
    },
  })

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const info = await uploadTemplate(file)
      setTemplateInfo(info)
      setZones([])
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async () => {
    setLoading(true)
    setError(null)
    try {
      const samples = await fetchPreviews(buildSynthesisConfig())
      setPreviews(samples)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleReroll = async (idx: number) => {
    const seed = 1000 + idx
    try {
      const samples = await fetchPreviews(buildSynthesisConfig(), [seed])
      setPreviews(prev => {
        const next = [...prev]
        next[idx] = samples[0]
        return next
      })
    } catch (err) {
      setError(String(err))
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setJobStatus(null)
    setDownloadJobId(null)
    try {
      const jobId = await startGenerate(buildSynthesisConfig(), generateN)
      const poll = setInterval(async () => {
        const status = await getJobStatus(jobId)
        setJobStatus(status)
        if (status.status === 'done') {
          clearInterval(poll)
          setDownloadJobId(jobId)
          setLoading(false)
        } else if (status.status === 'failed') {
          clearInterval(poll)
          setError(status.error ?? 'Generation failed')
          setLoading(false)
        }
      }, 2000)
    } catch (err) {
      setError(String(err))
      setLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <h1>Synthetic Document Generator &mdash; Zone Editor</h1>

      {/* Status bar */}
      {error && <div style={{ color: 'red', marginBottom: 12 }}>Error: {error}</div>}
      {loading && <div style={{ color: '#555', marginBottom: 12 }}>Loading...</div>}

      {/* Template upload */}
      <section style={{ marginBottom: 24 }}>
        <h2>1. Upload Template</h2>
        <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={handleFileChange} />
        {templateInfo && (
          <div style={{ marginTop: 8, color: '#333' }}>
            Loaded: {templateInfo.width_px} &times; {templateInfo.height_px} px
            {templateInfo.is_pdf ? ' (PDF)' : ' (Image)'}
          </div>
        )}
      </section>

      {/* Template preview (static img - Konva canvas is Future Work) */}
      {templateInfo && (
        <section style={{ marginBottom: 24 }}>
          <h2>2. Document Canvas</h2>
          <p style={{ color: '#777', fontSize: 13 }}>
            Zone drawing via Konva canvas &mdash; coming soon. Template is loaded and visible below.
          </p>
          <img
            src={`data:image/png;base64,${templateInfo.image_b64}`}
            alt="Template"
            style={{ maxWidth: '100%', border: '1px solid #ccc', display: 'block' }}
          />
        </section>
      )}

      {/* Respondents */}
      <section style={{ marginBottom: 24 }}>
        <h2>3. Respondents</h2>
        {respondents.map((r, ri) => (
          <div key={r.respondent_id} style={{ border: '1px solid #ddd', padding: 12, marginBottom: 8 }}>
            <label>Name: <input
              value={r.display_name}
              onChange={e => setRespondents(prev => {
                const next = [...prev]
                next[ri] = { ...next[ri], display_name: e.target.value }
                return next
              })}
            /></label>
            {respondents.length > 1 && (
              <button onClick={() => setRespondents(prev => prev.filter((_, i) => i !== ri))} style={{ marginLeft: 8 }}>
                Remove
              </button>
            )}
          </div>
        ))}
        <button onClick={() => setRespondents(prev => [...prev, {
          ...DEFAULT_RESPONDENT,
          respondent_id: `person_${prev.length}`,
          display_name: `Person ${prev.length + 1}`,
        }])}>
          + Add Respondent
        </button>
      </section>

      {/* Preview */}
      <section style={{ marginBottom: 24 }}>
        <h2>4. Preview</h2>
        <button onClick={handlePreview} disabled={loading}>Preview (3 samples)</button>
        {previews.length > 0 && (
          <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
            {previews.map((sample, i) => (
              <div key={sample.seed} style={{ textAlign: 'center' }}>
                <img
                  src={`data:image/png;base64,${sample.image_b64}`}
                  alt={`Sample seed=${sample.seed}`}
                  style={{ width: 250, border: '1px solid #ccc', display: 'block' }}
                />
                <div style={{ fontSize: 12, color: '#777' }}>seed={sample.seed}</div>
                <button onClick={() => handleReroll(i)} style={{ marginTop: 4 }}>&#8635; Re-roll</button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Batch generate */}
      <section style={{ marginBottom: 24 }}>
        <h2>5. Generate Batch</h2>
        <label>
          Count: <input type="number" min={1} value={generateN} onChange={e => setGenerateN(Number(e.target.value))} style={{ width: 80 }} />
        </label>
        {' '}
        <label>
          Output dir: <input value={outputDir} onChange={e => setOutputDir(e.target.value)} style={{ width: 300 }} />
        </label>
        {' '}
        <button onClick={handleGenerate} disabled={loading}>Generate</button>

        {jobStatus && (
          <div style={{ marginTop: 8 }}>
            Status: {jobStatus.status} ({Math.round(jobStatus.progress * 100)}%)
          </div>
        )}
        {downloadJobId && (
          <a href={downloadUrl(downloadJobId)} download="synthetic_documents.zip" style={{ display: 'inline-block', marginTop: 8 }}>
            Download ZIP
          </a>
        )}
      </section>
    </div>
  )
}
