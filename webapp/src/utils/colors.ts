const RESPONDENT_COLORS = [
  '#3498db', // blue
  '#e74c3c', // red
  '#2ecc71', // green
  '#f39c12', // orange
  '#9b59b6', // purple
  '#1abc9c', // teal
  '#e67e22', // dark-orange
  '#e91e63', // pink
]

export function getRespondentColor(index: number): string {
  return RESPONDENT_COLORS[index % RESPONDENT_COLORS.length]
}
