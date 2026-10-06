import { PUBLIC_API_URL, PUBLIC_APP_URL } from 'astro:env/client'
import { buildLinks } from './links'

export const links = buildLinks(PUBLIC_APP_URL, PUBLIC_API_URL)
