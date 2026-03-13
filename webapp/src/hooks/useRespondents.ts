import { useState } from 'react'
import type { RespondentConfig, FieldTypeConfig } from '../types'

const DEFAULT_FIELD_TYPE: FieldTypeConfig = {
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
}

const DEFAULT_RESPONDENT: RespondentConfig = {
  respondent_id: 'default',
  display_name: 'Default',
  field_types: [{ ...DEFAULT_FIELD_TYPE }],
}

export function useRespondents() {
  const [respondents, setRespondents] = useState<RespondentConfig[]>([DEFAULT_RESPONDENT])

  const addRespondent = () => {
    const idx = respondents.length
    setRespondents(prev => [
      ...prev,
      {
        respondent_id: `person_${idx}`,
        display_name: `Person ${idx + 1}`,
        field_types: [{ ...DEFAULT_FIELD_TYPE }],
      },
    ])
  }

  const removeRespondent = (respondent_id: string) => {
    setRespondents(prev => prev.filter(r => r.respondent_id !== respondent_id))
  }

  const updateRespondent = (respondent_id: string, patch: Partial<RespondentConfig>) => {
    setRespondents(prev =>
      prev.map(r => (r.respondent_id === respondent_id ? { ...r, ...patch } : r))
    )
  }

  const addFieldType = (respondent_id: string) => {
    setRespondents(prev =>
      prev.map(r => {
        if (r.respondent_id !== respondent_id) return r
        const idx = r.field_types.length
        return {
          ...r,
          field_types: [
            ...r.field_types,
            { ...DEFAULT_FIELD_TYPE, field_type_id: `ft_${idx}`, display_name: `Style ${idx + 1}` },
          ],
        }
      })
    )
  }

  const removeFieldType = (respondent_id: string, field_type_id: string) => {
    setRespondents(prev =>
      prev.map(r => {
        if (r.respondent_id !== respondent_id) return r
        return { ...r, field_types: r.field_types.filter(ft => ft.field_type_id !== field_type_id) }
      })
    )
  }

  const updateFieldType = (
    respondent_id: string,
    field_type_id: string,
    patch: Partial<FieldTypeConfig>
  ) => {
    setRespondents(prev =>
      prev.map(r => {
        if (r.respondent_id !== respondent_id) return r
        return {
          ...r,
          field_types: r.field_types.map(ft =>
            ft.field_type_id === field_type_id ? { ...ft, ...patch } : ft
          ),
        }
      })
    )
  }

  return {
    respondents,
    addRespondent,
    removeRespondent,
    updateRespondent,
    addFieldType,
    removeFieldType,
    updateFieldType,
  }
}
