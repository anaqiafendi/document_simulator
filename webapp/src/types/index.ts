export interface FieldTypeConfig {
  field_type_id: string
  display_name: string
  font_family: 'sans-serif' | 'serif' | 'monospace' | 'handwriting'
  font_size_range: [number, number]
  font_color: string
  bold: boolean
  italic: boolean
  fill_style: 'typed' | 'form-fill' | 'handwritten-font' | 'stamp'
  jitter_x: number
  jitter_y: number
  baseline_wander: number
  char_spacing_jitter: number
}

export interface RespondentConfig {
  respondent_id: string
  display_name: string
  field_types: FieldTypeConfig[]
}

export interface ZoneConfig {
  zone_id: string
  label: string
  box: number[][]  // [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
  respondent_id: string
  field_type_id: string
  faker_provider: string
  custom_values: string[]
  alignment: 'left' | 'center' | 'right'
  page: number  // 0-indexed PDF page this zone belongs to
}

export interface GeneratorConfig {
  image_width: number
  image_height: number
  output_dir: string
  seed: number
  n: number
}

export interface SynthesisConfig {
  respondents: RespondentConfig[]
  zones: ZoneConfig[]
  generator: GeneratorConfig
}

export interface TemplateInfo {
  image_b64: string
  width_px: number
  height_px: number
  dpi: number
  is_pdf: boolean
  page_count: number
  template_id: string | null
}

export interface PreviewSample {
  seed: number
  image_b64: string
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'running' | 'done' | 'failed'
  progress: number
  error: string | null
}

// ── Augmentation ─────────────────────────────────────────────────────────────

export interface AugmentMetadata {
  preset: string
  width: number
  height: number
  filename: string
}

export interface AugmentResult {
  original_b64: string
  augmented_b64: string
  metadata: AugmentMetadata
}

export interface CatalogueEntry {
  name: string
  display_name: string
  phase: 'ink' | 'paper' | 'post'
  description: string
  slow: boolean
  default_params: Record<string, unknown>
}

export interface CatalogueAugmentResult {
  original_b64: string
  augmented_b64: string
  aug_name: string
  display_name: string
  phase: string
}

export interface PipelineResult {
  original_b64: string
  augmented_b64: string
  applied: string[]
}

// ── OCR ──────────────────────────────────────────────────────────────────────

export interface OcrResult {
  text: string
  boxes: number[][][]
  scores: number[]
  mean_confidence: number
  n_regions: number
  annotated_b64: string
}

// ── Batch ────────────────────────────────────────────────────────────────────

export type BatchMode = 'single' | 'per_template' | 'random_sample'

export interface BatchJobStatus extends JobStatus {
  // inherits job_id, status, progress, error
}

// ── Evaluation ───────────────────────────────────────────────────────────────

export interface EvalMetrics {
  n_samples: number
  mean_original_cer: number
  mean_augmented_cer: number
  mean_original_wer: number
  mean_augmented_wer: number
  mean_original_confidence: number
  mean_augmented_confidence: number
  std_original_cer: number
  std_augmented_cer: number
  std_original_wer: number
  std_augmented_wer: number
  std_original_confidence: number
  std_augmented_confidence: number
}

export interface EvalJobStatus extends JobStatus {
  results: EvalMetrics | null
}

// ── RL Training ──────────────────────────────────────────────────────────────

export interface RewardPoint {
  step: number
  reward: number
}

export interface RlJobStatus extends JobStatus {
  step: number
  reward: number
  model_path: string | null
}

export interface RlMetrics {
  job_id: string
  reward_curve: RewardPoint[]
}

export interface RlTrainConfig {
  learning_rate: number
  batch_size: number
  n_steps: number
  num_envs: number
  total_timesteps: number
  checkpoint_freq: number
  dataset_dir: string | null
}
