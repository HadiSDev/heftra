export interface SiteLinks {
  signIn: string
  demo: string
  demoRequestEndpoint: string
}

function withoutTrailingSlash(url: string): string {
  return url.replace(/\/+$/, '')
}

export function buildLinks(appUrl: string, apiUrl: string): SiteLinks {
  return {
    signIn: `${withoutTrailingSlash(appUrl)}/sign-in`,
    demo: '/demo/',
    demoRequestEndpoint: `${withoutTrailingSlash(apiUrl)}/api/v1/public/demo-requests`,
  }
}
