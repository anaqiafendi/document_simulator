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
