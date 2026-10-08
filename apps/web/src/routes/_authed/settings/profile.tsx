import { createFileRoute } from '@tanstack/react-router'
import { useUser } from '@clerk/tanstack-react-start'
import { Skeleton } from '#/components/ui'
import { EmailsPanel } from '#/components/settings/profile/emails-panel'
import { PreferencesPanel } from '#/components/settings/profile/preferences-panel'
import { ProfilePanel } from '#/components/settings/profile/profile-panel'
import { SecurityPanel } from '#/components/settings/profile/security-panel'
import { usePrincipal } from '#/lib/auth/auth'
import { useDemoGuard } from '#/lib/demo/use-demo-guard'

export const Route = createFileRoute('/_authed/settings/profile')({
  component: ProfileSection,
})

function ProfileSection() {
  const { user, isLoaded } = useUser()
  const principal = usePrincipal()
  const guard = useDemoGuard()

  if (!isLoaded || !user) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-64 rounded-card" />
        <Skeleton className="h-48 rounded-card" />
      </div>
    )
  }

  const email = user.primaryEmailAddress?.emailAddress ?? principal.email

  return (
    <div className="flex flex-col gap-6">
      <ProfilePanel
        defaultValues={{
          firstName: user.firstName ?? '',
          lastName: user.lastName ?? '',
        }}
        displayName={user.fullName || user.username || principal.name}
        email={email}
        imageUrl={user.hasImage ? user.imageUrl : undefined}
        onSave={guard(({ firstName, lastName }) =>
          user.update({ firstName, lastName }),
        )}
        onUploadImage={guard((file) => user.setProfileImage({ file }))}
        onRemoveImage={guard(() => user.setProfileImage({ file: null }))}
      />
      <EmailsPanel user={user} />
      <SecurityPanel user={user} />
      <PreferencesPanel />
    </div>
  )
}
