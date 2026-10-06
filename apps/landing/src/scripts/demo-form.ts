interface ValidationIssue {
  loc: Array<string | number>
  msg: string
}

interface DemoRequestAccepted {
  booking_url: string | null
}

const fieldNames = [
  'name',
  'email',
  'company',
  'company_size',
  'message',
  'consent',
] as const

type FieldName = (typeof fieldNames)[number]

function isFieldName(value: unknown): value is FieldName {
  return (
    typeof value === 'string' &&
    (fieldNames as ReadonlyArray<string>).includes(value)
  )
}

function fieldControl(
  form: HTMLFormElement,
  name: FieldName,
): HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | null {
  return form.querySelector(`[name="${name}"]`)
}

function fieldErrorElement(
  form: HTMLFormElement,
  name: FieldName,
): HTMLElement | null {
  return form.querySelector(`#demo-${name}-error`)
}

function showFieldError(
  form: HTMLFormElement,
  name: FieldName,
  message: string,
): void {
  const control = fieldControl(form, name)
  const error = fieldErrorElement(form, name)
  control?.setAttribute('aria-invalid', 'true')
  if (error) {
    error.textContent = message
    error.classList.remove('hidden')
  }
}

function clearErrors(form: HTMLFormElement, formError: HTMLElement): void {
  fieldNames.forEach((name) => {
    fieldControl(form, name)?.removeAttribute('aria-invalid')
    const error = fieldErrorElement(form, name)
    if (error) {
      error.textContent = ''
      error.classList.add('hidden')
    }
  })
  formError.textContent = ''
  formError.classList.add('hidden')
}

function clientSideErrors(form: HTMLFormElement): Map<FieldName, string> {
  const errors = new Map<FieldName, string>()
  const value = (name: FieldName) =>
    (fieldControl(form, name)?.value ?? '').trim()

  if (!value('name')) {
    errors.set('name', 'Enter your name.')
  }
  if (!value('email')) {
    errors.set('email', 'Enter your work email.')
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value('email'))) {
    errors.set('email', 'Enter a valid email address, like name@company.com.')
  }
  if (!value('company')) {
    errors.set('company', 'Enter your company name.')
  }
  if (!value('company_size')) {
    errors.set('company_size', 'Choose your company size.')
  }
  const consent = fieldControl(form, 'consent')
  if (consent instanceof HTMLInputElement && !consent.checked) {
    errors.set('consent', 'Please agree so we can contact you about the demo.')
  }
  return errors
}

function serverErrors(issues: Array<ValidationIssue>): Map<FieldName, string> {
  const errors = new Map<FieldName, string>()
  issues.forEach((issue) => {
    const field = issue.loc[issue.loc.length - 1]
    if (isFieldName(field) && !errors.has(field)) {
      errors.set(field, issue.msg.replace(/^Value error, /, ''))
    }
  })
  return errors
}

function presentFieldErrors(
  form: HTMLFormElement,
  errors: Map<FieldName, string>,
): void {
  errors.forEach((message, name) => {
    showFieldError(form, name, message)
  })
  const first = fieldNames.find((name) => errors.has(name))
  if (first) {
    fieldControl(form, first)?.focus()
  }
}

function payload(form: HTMLFormElement, renderedAt: number) {
  const data = new FormData(form)
  const text = (name: string) => String(data.get(name) ?? '').trim()
  const message = text('message')
  return {
    name: text('name'),
    email: text('email'),
    company: text('company'),
    company_size: text('company_size'),
    message: message === '' ? null : message,
    consent: data.get('consent') === 'on',
    website: text('website'),
    rendered_at: renderedAt,
  }
}

function setSubmitting(form: HTMLFormElement, submitting: boolean): void {
  const button = form.querySelector<HTMLButtonElement>('[data-submit]')
  const label = form.querySelector<HTMLElement>('[data-submit-label]')
  if (button) {
    button.disabled = submitting
  }
  if (label) {
    label.textContent = submitting ? 'Sending…' : 'Request my demo'
  }
}

function showConfirmation(
  root: HTMLElement,
  form: HTMLFormElement,
  bookingUrl: string | null,
): void {
  const confirmation = root.querySelector<HTMLElement>(
    '[data-demo-confirmation]',
  )
  const bookingLink = root.querySelector<HTMLAnchorElement>(
    '[data-booking-link]',
  )
  const text = root.querySelector<HTMLElement>('[data-confirmation-text]')
  const liveRegion = root.querySelector<HTMLElement>('[data-live-region]')
  if (!confirmation) {
    return
  }

  if (bookingUrl && bookingLink) {
    bookingLink.href = bookingUrl
    bookingLink.classList.remove('hidden')
    bookingLink.classList.add('inline-flex')
  } else if (text) {
    text.textContent =
      'We will email you within one business day to find a time that suits you.'
  }

  form.classList.add('hidden')
  form.classList.remove('flex')
  confirmation.classList.remove('hidden')
  confirmation.classList.add('flex')
  confirmation.focus()
  if (liveRegion) {
    liveRegion.textContent = 'Your demo request has been sent.'
  }
}

function initForm(root: HTMLElement): void {
  const form = root.querySelector<HTMLFormElement>('[data-demo-form]')
  const formError = root.querySelector<HTMLElement>('[data-form-error]')
  if (!form || !formError) {
    return
  }
  const endpoint = form.dataset.endpoint ?? ''
  const contactEmail = form.dataset.contactEmail ?? ''
  const renderedAt = Date.now()

  form.classList.remove('hidden')
  form.classList.add('flex')

  const showFormError = (message: string) => {
    formError.textContent = message
    formError.classList.remove('hidden')
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    clearErrors(form, formError)

    const localErrors = clientSideErrors(form)
    if (localErrors.size > 0) {
      presentFieldErrors(form, localErrors)
      return
    }

    setSubmitting(form, true)
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload(form, renderedAt)),
      })
      if (response.status === 201) {
        const body = (await response.json()) as DemoRequestAccepted
        showConfirmation(root, form, body.booking_url)
        return
      }
      if (response.status === 422) {
        const body = (await response.json()) as {
          detail?: Array<ValidationIssue>
        }
        const errors = serverErrors(body.detail ?? [])
        if (errors.size > 0) {
          presentFieldErrors(form, errors)
          return
        }
      }
      if (response.status === 429) {
        showFormError(
          `You have sent several requests in a short time. Please try again later, or write to ${contactEmail}.`,
        )
        return
      }
      showFormError(
        `Something went wrong on our side. Please try again, or write to ${contactEmail}.`,
      )
    } catch {
      showFormError(
        `We could not reach our server. Check your connection and try again, or write to ${contactEmail}.`,
      )
    } finally {
      setSubmitting(form, false)
    }
  })
}

export function initDemoForm(): void {
  document
    .querySelectorAll<HTMLElement>('[data-demo-form-root]')
    .forEach(initForm)
}
