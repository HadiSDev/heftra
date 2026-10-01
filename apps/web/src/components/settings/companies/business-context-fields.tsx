import type { UseFormReturn } from 'react-hook-form'
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  Input,
  Textarea,
} from '#/components/ui'
import type { CompanyRead } from '#/lib/api/types'
import type { CompanyFormValues } from './company-values'

function descriptionHint(
  company: CompanyRead | null,
  description: string,
): string {
  if (
    company?.description_source === 'web' &&
    description === company.description
  ) {
    return 'Researched from the website. Correct it if it misses what you do; what you write is kept.'
  }
  if (!description && company?.website) {
    return 'The website is being read to describe the company. You can also write it yourself.'
  }
  if (!description) {
    return 'Leave it empty to have it researched from the website.'
  }
  return 'Written by your team; it is never replaced by research.'
}

/** The company's website and what it does, which the AI reads with its spend and agreements. */
export function BusinessContextFields({
  form,
  company,
}: {
  form: UseFormReturn<CompanyFormValues>
  company: CompanyRead | null
}) {
  const description = form.watch('description')
  return (
    <>
      <FormField
        control={form.control}
        name="website"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Website</FormLabel>
            <FormControl>
              <Input {...field} placeholder="example.com" inputMode="url" />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="description"
        rules={{
          maxLength: {
            value: 2000,
            message: 'Keep it under 2,000 characters.',
          },
        }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>What the company does</FormLabel>
            <FormControl>
              <Textarea
                {...field}
                rows={3}
                placeholder="We build data and AI products, and test apps on phones and smartwatches."
              />
            </FormControl>
            <FormDescription>
              Categorization and agreement checks read this to judge what a
              purchase is to you. {descriptionHint(company, description)}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  )
}
