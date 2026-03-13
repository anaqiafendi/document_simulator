import { useState } from 'react'
import type { JobStatus } from '../types'

interface Props {
  loading: boolean
  jobStatus: JobStatus | null
  downloadJobId: string | null
  onGenerate: (n: number, outputDir: string) => void
  downloadUrl: (jobId: string) => string
}

export default function BatchGeneratePanel({
  loading,
  jobStatus,
  downloadJobId,
  onGenerate,
  downloadUrl,
}: Props) {
  const [n, setN] = useState(10)
  const [outputDir, setOutputDir] = useState('/tmp/synthetic_output')

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <label style={{ fontSize: 13 }}>
          Count:{' '}
          <input
            type="number"
            min={1}
            value={n}
            onChange={e => setN(Number(e.target.value))}
            style={{ width: 70 }}
          />
        </label>
        <label style={{ fontSize: 13 }}>
          Output dir:{' '}
          <input
            value={outputDir}
            onChange={e => setOutputDir(e.target.value)}
            style={{ width: 260 }}
          />
        </label>
        <button onClick={() => onGenerate(n, outputDir)} disabled={loading}>
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </div>
      {jobStatus && (
        <div style={{ marginTop: 8, fontSize: 13, color: '#555' }}>
          Status: <b>{jobStatus.status}</b> ({Math.round(jobStatus.progress * 100)}%)
        </div>
      )}
      {downloadJobId && (
        <a
          href={downloadUrl(downloadJobId)}
          download="synthetic_documents.zip"
          style={{ display: 'inline-block', marginTop: 8, fontSize: 13 }}
        >
          Download ZIP
        </a>
      )}
    </div>
  )
}
