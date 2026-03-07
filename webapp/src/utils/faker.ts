import { faker } from '@faker-js/faker'

export const FAKER_PROVIDERS: { key: string; label: string; generate: () => string }[] = [
  { key: 'name',               label: 'Full name',          generate: () => faker.person.fullName() },
  { key: 'first_name',         label: 'First name',         generate: () => faker.person.firstName() },
  { key: 'last_name',          label: 'Last name',          generate: () => faker.person.lastName() },
  { key: 'email',              label: 'Email',              generate: () => faker.internet.email() },
  { key: 'phone_number',       label: 'Phone',              generate: () => faker.phone.number() },
  { key: 'address',            label: 'Address',            generate: () => faker.location.streetAddress() },
  { key: 'city',               label: 'City',               generate: () => faker.location.city() },
  { key: 'postcode',           label: 'Postcode',           generate: () => faker.location.zipCode() },
  { key: 'company',            label: 'Company',            generate: () => faker.company.name() },
  { key: 'date_of_birth',      label: 'Date of birth',      generate: () => faker.date.birthdate().toLocaleDateString() },
  { key: 'ssn',                label: 'SSN',                generate: () => faker.string.numeric({ length: 9 }) },
  { key: 'credit_card_number', label: 'Credit card',        generate: () => faker.finance.creditCardNumber() },
  { key: 'sentence',           label: 'Sentence',           generate: () => faker.lorem.sentence() },
  { key: 'word',               label: 'Word',               generate: () => faker.lorem.word() },
  { key: 'custom',             label: 'Custom',             generate: () => 'Custom text' },
]

export function generateFakerValue(provider: string): string {
  const p = FAKER_PROVIDERS.find(p => p.key === provider)
  return p ? p.generate() : provider
}

export function fakerLabel(provider: string): string {
  return FAKER_PROVIDERS.find(p => p.key === provider)?.label ?? provider
}
