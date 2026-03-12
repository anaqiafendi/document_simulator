import { faker } from '@faker-js/faker'

export const FAKER_PROVIDERS: { key: string; label: string; group?: string; generate: () => string }[] = [
  // ── Identity ────────────────────────────────────────────────────────────
  { key: 'name',               label: 'Full name',              group: 'Identity',  generate: () => faker.person.fullName() },
  { key: 'first_name',         label: 'First name',             group: 'Identity',  generate: () => faker.person.firstName() },
  { key: 'last_name',          label: 'Last name',              group: 'Identity',  generate: () => faker.person.lastName() },
  { key: 'email',              label: 'Email',                  group: 'Identity',  generate: () => faker.internet.email() },
  { key: 'phone_number',       label: 'Phone',                  group: 'Identity',  generate: () => faker.phone.number() },
  { key: 'ssn',                label: 'SSN',                    group: 'Identity',  generate: () => faker.string.numeric({ length: 9 }) },
  { key: 'company',            label: 'Company',                group: 'Identity',  generate: () => faker.company.name() },
  // ── Address ─────────────────────────────────────────────────────────────
  { key: 'address',            label: 'Street address',         group: 'Address',   generate: () => faker.location.streetAddress() },
  { key: 'address_single_line',label: 'Full address (1 line)',  group: 'Address',   generate: () => `${faker.location.streetAddress()}, ${faker.location.city()}, ${faker.location.state({ abbreviated: true })} ${faker.location.zipCode()}` },
  { key: 'city',               label: 'City',                   group: 'Address',   generate: () => faker.location.city() },
  { key: 'postcode',           label: 'Postcode',               group: 'Address',   generate: () => faker.location.zipCode() },
  // ── Numbers & Prices ────────────────────────────────────────────────────
  { key: 'price_short',        label: 'Price (short, <$100)',   group: 'Numbers',   generate: () => faker.commerce.price({ min: 1, max: 99, dec: 2, symbol: '$' }) },
  { key: 'price_medium',       label: 'Price (medium, <$10k)',  group: 'Numbers',   generate: () => faker.commerce.price({ min: 100, max: 9999, dec: 2, symbol: '$' }) },
  { key: 'price_large',        label: 'Price (large, <$1M)',    group: 'Numbers',   generate: () => faker.commerce.price({ min: 10000, max: 999999, dec: 2, symbol: '$' }) },
  { key: 'number_short',       label: 'Number (3–5 digits)',    group: 'Numbers',   generate: () => faker.string.numeric({ length: { min: 3, max: 5 } }) },
  { key: 'number_medium',      label: 'Number (6–9 digits)',    group: 'Numbers',   generate: () => faker.string.numeric({ length: { min: 6, max: 9 } }) },
  { key: 'number_long',        label: 'Number (10–14 digits)',  group: 'Numbers',   generate: () => faker.string.numeric({ length: { min: 10, max: 14 } }) },
  { key: 'credit_card_number', label: 'Credit card',           group: 'Numbers',   generate: () => faker.finance.creditCardNumber() },
  // ── Dates ───────────────────────────────────────────────────────────────
  { key: 'date_of_birth',      label: 'Date of birth',          group: 'Dates',     generate: () => faker.date.birthdate().toLocaleDateString('en-US') },
  { key: 'date_numeric',       label: 'Date (MM/DD/YYYY)',       group: 'Dates',     generate: () => faker.date.recent().toLocaleDateString('en-US') },
  { key: 'date_written',       label: 'Date (written)',          group: 'Dates',     generate: () => faker.date.recent().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) },
  { key: 'signing_date',       label: 'Signing date',           group: 'Dates',     generate: () => faker.date.recent().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) },
  { key: 'effective_date',     label: 'Effective date',         group: 'Dates',     generate: () => faker.date.soon({ days: 30 }).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) },
  { key: 'termination_date',   label: 'Contract termination date', group: 'Dates',  generate: () => faker.date.future({ years: 3 }).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) },
  // ── Signature ───────────────────────────────────────────────────────────
  { key: 'signature',          label: 'Signature (handwritten)', group: 'Signature', generate: () => faker.person.fullName() },
  // ── Checkbox ────────────────────────────────────────────────────────────
  { key: 'checkbox_checked',   label: 'Checkbox ☑ (checked)',   group: 'Checkbox',  generate: () => '☑' },
  { key: 'checkbox_unchecked', label: 'Checkbox ☐ (unchecked)', group: 'Checkbox',  generate: () => '☐' },
  { key: 'checkbox_x',         label: 'Checkbox ☒ (X-mark)',    group: 'Checkbox',  generate: () => '☒' },
  // ── Text ────────────────────────────────────────────────────────────────
  { key: 'sentence',           label: 'Sentence',               group: 'Text',      generate: () => faker.lorem.sentence() },
  { key: 'word',               label: 'Word',                   group: 'Text',      generate: () => faker.lorem.word() },
  { key: 'custom',             label: 'Custom',                 group: 'Text',      generate: () => 'Custom text' },
]

export function generateFakerValue(provider: string): string {
  const p = FAKER_PROVIDERS.find(p => p.key === provider)
  return p ? p.generate() : provider
}

export function fakerLabel(provider: string): string {
  return FAKER_PROVIDERS.find(p => p.key === provider)?.label ?? provider
}
