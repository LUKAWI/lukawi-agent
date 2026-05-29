import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

let reducedMotion = false;

gsap.defaults({
  duration: 0.4,
  ease: "power2.out",
});

const mm = gsap.matchMedia();

mm.add(
  {
    reduceMotion: "(prefers-reduced-motion: reduce)",
    noPreference: "(prefers-reduced-motion: no-preference)",
  },
  (context) => {
    const { reduceMotion: rm } = context.conditions!;
    reducedMotion = rm;

    if (rm) {
      gsap.defaults({ duration: 0, ease: "none" });
    }
  },
);

/**
 * Get duration respecting reduced-motion preference.
 * Use this in components: `duration: getDuration(0.4)`
 */
function getDuration(preferred: number): number {
  return reducedMotion ? 0 : preferred;
}

export { gsap, useGSAP, mm, reducedMotion, getDuration };
