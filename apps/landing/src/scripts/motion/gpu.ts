export function releaseWillChange(this: gsap.core.Tween): void {
  this.targets<HTMLElement>().forEach((target) => {
    target.style.willChange = ''
  })
}
