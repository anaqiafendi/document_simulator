import type { TemplateInfo, SynthesisConfig, PreviewSample, JobStatus } from '../types'

const BASE = ''  // same origin in prod; proxied in dev

export async function uploadTemplate(file: File, dpi = 150, page = 0): Promise<TemplateInfo> {
  const form = new FormData()
  form.append('file', file)
  form.append('dpi', String(dpi))
  form.append('page', String(page))
  const r = await fetch(`${BASE}/api/template`, { method: 'POST', body: form })
  if (!r.ok) throw new Error(`Template upload failed: ${r.status}`)
  return r.json()
}

export async function fetchPreviews(
  synthesisConfig: SynthesisConfig,
  seeds: number[] = [42, 43, 44]
): Promise<PreviewSample[]> {
  const r = await fetch(`${BASE}/api/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synthesis_config: synthesisConfig, seeds }),
  })
  if (!r.ok) throw new Error(`Preview failed: ${r.status}`)
  const data = await r.json()
  return data.samples
}

export async function startGenerate(synthesisConfig: SynthesisConfig, n: number): Promise<string> {
  const r = await fetch(`${BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synthesis_config: synthesisConfig, n }),
  })
  if (!r.ok) throw new Error(`Generate failed: ${r.status}`)
  const data = await r.json()
  return data.job_id
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const r = await fetch(`${BASE}/api/jobs/${jobId}`)
  if (!r.ok) throw new Error(`Job status failed: ${r.status}`)
  return r.json()
}

export function downloadUrl(jobId: string): string {
  return `${BASE}/api/jobs/${jobId}/download`
}
