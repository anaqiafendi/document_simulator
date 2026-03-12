import type {
  TemplateInfo,
  SynthesisConfig,
  PreviewSample,
  JobStatus,
  AugmentResult,
  OcrResult,
  BatchMode,
  BatchJobStatus,
  EvalJobStatus,
  RlTrainConfig,
  RlJobStatus,
  RlMetrics,
} from '../types'

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

export async function listSamples(): Promise<string[]> {
  const r = await fetch(`${BASE}/api/samples`)
  if (!r.ok) throw new Error(`Failed to list samples: ${r.status}`)
  const data = await r.json()
  return data.samples as string[]
}

export async function loadSample(filename: string, dpi = 150, page = 0): Promise<TemplateInfo> {
  const r = await fetch(`${BASE}/api/samples/${encodeURIComponent(filename)}?dpi=${dpi}&page=${page}`)
  if (!r.ok) throw new Error(`Failed to load sample: ${r.status}`)
  return r.json()
}

export async function fetchPreviews(
  synthesisConfig: SynthesisConfig,
  seeds: number[] = [42, 43, 44],
  templateB64?: string,
  currentPage = 0,
): Promise<PreviewSample[]> {
  const r = await fetch(`${BASE}/api/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synthesis_config: synthesisConfig, seeds, template_b64: templateB64 ?? null, current_page: currentPage }),
  })
  if (!r.ok) throw new Error(`Preview failed: ${r.status}`)
  const data = await r.json()
  return data.samples
}

export async function startGenerate(
  synthesisConfig: SynthesisConfig,
  n: number,
  templateB64?: string,
  templateId?: string | null,
): Promise<string> {
  const r = await fetch(`${BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      synthesis_config: synthesisConfig,
      n,
      template_b64: templateB64 ?? null,
      template_id: templateId ?? null,
    }),
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

// ── Augmentation ─────────────────────────────────────────────────────────────

export async function listPresets(): Promise<string[]> {
  const r = await fetch(`${BASE}/api/augmentation/presets`)
  if (!r.ok) throw new Error(`Failed to list presets: ${r.status}`)
  const data = await r.json()
  return data.presets as string[]
}

export async function augmentImage(file: File, preset: string): Promise<AugmentResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('preset', preset)
  const r = await fetch(`${BASE}/api/augmentation/augment`, { method: 'POST', body: form })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error(`Augmentation failed: ${detail.detail ?? r.status}`)
  }
  return r.json()
}

// ── OCR ──────────────────────────────────────────────────────────────────────

export async function recognizeOcr(file: File, lang = 'en', useGpu = false): Promise<OcrResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('lang', lang)
  form.append('use_gpu', String(useGpu))
  const r = await fetch(`${BASE}/api/ocr/recognize`, { method: 'POST', body: form })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error(`OCR failed: ${detail.detail ?? r.status}`)
  }
  return r.json()
}

// ── Batch ────────────────────────────────────────────────────────────────────

export interface BatchProcessOptions {
  preset?: string
  mode?: BatchMode
  copiesPerTemplate?: number
  totalOutputs?: number
  seed?: number
  nWorkers?: number
}

export async function startBatchProcess(files: File[], opts: BatchProcessOptions = {}): Promise<string> {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  form.append('preset', opts.preset ?? 'medium')
  form.append('mode', opts.mode ?? 'single')
  form.append('copies_per_template', String(opts.copiesPerTemplate ?? 3))
  form.append('total_outputs', String(opts.totalOutputs ?? 20))
  form.append('seed', String(opts.seed ?? 0))
  form.append('n_workers', String(opts.nWorkers ?? 4))
  const r = await fetch(`${BASE}/api/batch/process`, { method: 'POST', body: form })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error(`Batch process failed: ${detail.detail ?? r.status}`)
  }
  const data = await r.json()
  return data.job_id as string
}

export async function getBatchJobStatus(jobId: string): Promise<BatchJobStatus> {
  const r = await fetch(`${BASE}/api/batch/jobs/${jobId}`)
  if (!r.ok) throw new Error(`Batch job status failed: ${r.status}`)
  return r.json()
}

export function batchDownloadUrl(jobId: string): string {
  return `${BASE}/api/batch/jobs/${jobId}/download`
}

// ── Evaluation ────────────────────────────────────────────────────────────────

export async function startEvaluation(
  preset: string,
  zipFile?: File,
  datasetDir?: string,
  useGpu = false,
): Promise<string> {
  const form = new FormData()
  form.append('preset', preset)
  form.append('use_gpu', String(useGpu))
  if (zipFile) form.append('zip_file', zipFile)
  if (datasetDir) form.append('dataset_dir', datasetDir)
  const r = await fetch(`${BASE}/api/evaluation/run`, { method: 'POST', body: form })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error(`Evaluation failed: ${detail.detail ?? r.status}`)
  }
  const data = await r.json()
  return data.job_id as string
}

export async function getEvaluationStatus(jobId: string): Promise<EvalJobStatus> {
  const r = await fetch(`${BASE}/api/evaluation/jobs/${jobId}/status`)
  if (!r.ok) throw new Error(`Eval status failed: ${r.status}`)
  return r.json()
}

// ── RL Training ──────────────────────────────────────────────────────────────

export async function startRlTraining(config: RlTrainConfig): Promise<string> {
  const r = await fetch(`${BASE}/api/rl/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error(`RL training failed: ${detail.detail ?? r.status}`)
  }
  const data = await r.json()
  return data.job_id as string
}

export async function getRlJobStatus(jobId: string): Promise<RlJobStatus> {
  const r = await fetch(`${BASE}/api/rl/jobs/${jobId}/status`)
  if (!r.ok) throw new Error(`RL status failed: ${r.status}`)
  return r.json()
}

export async function getRlMetrics(jobId: string): Promise<RlMetrics> {
  const r = await fetch(`${BASE}/api/rl/jobs/${jobId}/metrics`)
  if (!r.ok) throw new Error(`RL metrics failed: ${r.status}`)
  return r.json()
}

export async function stopRlTraining(jobId: string): Promise<void> {
  await fetch(`${BASE}/api/rl/jobs/${jobId}/stop`, { method: 'POST' })
}
