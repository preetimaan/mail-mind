/**
 * Wall-calendar helpers: analysis ranges are logical calendar days, not UTC instants.
 * Never use Date.toISOString() for API bounds — it shifts local midnight into the previous/next UTC day.
 */

export function formatLocalYmd(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Parse API datetime string using only the Y-M-D part as local calendar midnight */
export function parseApiDateOnly(isoLike: string): Date {
  const head = isoLike.includes('T') ? isoLike.split('T')[0]! : isoLike.slice(0, 10)
  const parts = head.split('-').map(Number)
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) {
    return new Date(NaN)
  }
  const [y, mo, d] = parts
  return new Date(y, mo - 1, d, 0, 0, 0, 0)
}
