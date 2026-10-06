export interface DraftableEntry {
  id: string
  data: { draft: boolean }
}

export function assertNoDrafts(
  collection: string,
  entries: Array<DraftableEntry>,
  isProduction: boolean,
): void {
  if (!isProduction) {
    return
  }
  const drafts = entries
    .filter((entry) => entry.data.draft)
    .map((entry) => entry.id)
  if (drafts.length > 0) {
    throw new Error(
      `Draft ${collection} entries cannot be published: ${drafts.join(', ')}. Approve the figures and set draft: false.`,
    )
  }
}
