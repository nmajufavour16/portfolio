document.addEventListener('DOMContentLoaded', () => {
    // Mouse-spotlight glow — used on tech arsenal icons, cert cards, and
    // timeline items. Runs regardless of whether GSAP loaded, since it's
    // just a CSS custom-property update, not an animation library.
    document.querySelectorAll('[data-spotlight]').forEach((el) => {
        el.addEventListener('mousemove', (e) => {
            const rect = el.getBoundingClientRect();
            el.style.setProperty('--mx', `${e.clientX - rect.left}px`);
            el.style.setProperty('--my', `${e.clientY - rect.top}px`);
        });
    });

    const hasGsap = window.gsap && window.ScrollTrigger;

    // Smooth scroll — synced to GSAP's ticker rather than its own rAF loop,
    // so ScrollTrigger stays perfectly in step with it.
    if (window.Lenis) {
        const lenis = new Lenis();

        if (hasGsap) {
            lenis.on('scroll', ScrollTrigger.update);
            gsap.ticker.add((time) => lenis.raf(time * 1000));
            gsap.ticker.lagSmoothing(0);
        } else {
            const raf = (time) => {
                lenis.raf(time);
                requestAnimationFrame(raf);
            };
            requestAnimationFrame(raf);
        }
    }

    if (!hasGsap) return;
    gsap.registerPlugin(ScrollTrigger);

    // Generic fade/rise-in reveal for anything marked [data-reveal]
    gsap.utils.toArray('[data-reveal]').forEach((el) => {
        gsap.from(el, {
            opacity: 0,
            y: 24,
            duration: 0.8,
            ease: 'power2.out',
            scrollTrigger: { trigger: el, start: 'top 85%' },
        });
    });

    // Count-up stats (years experience, tech skills, projects, visitors)
    gsap.utils.toArray('[data-counter]').forEach((el) => {
        const target = parseInt(el.dataset.target, 10) || 0;
        const counter = { val: 0 };
        gsap.to(counter, {
            val: target,
            duration: 1.4,
            ease: 'power1.out',
            scrollTrigger: { trigger: el, start: 'top 90%', once: true },
            onUpdate: () => {
                el.textContent = Math.round(counter.val);
            },
        });
    });

    // Skill proficiency bars — fill from 0 to their target % on scroll into view
    gsap.utils.toArray('[data-progress]').forEach((el) => {
        const target = el.dataset.progress;
        gsap.to(el, {
            width: `${target}%`,
            duration: 1,
            ease: 'power2.out',
            scrollTrigger: { trigger: el, start: 'top 90%', once: true },
        });
    });

    // Timeline "drawing line" — fills top to bottom in step with scroll
    // position through the whole timeline, rather than fading in all at once
    gsap.utils.toArray('[data-timeline-fill]').forEach((el) => {
        const wrapper = el.closest('.timeline__wrapper');
        if (!wrapper) return;
        gsap.to(el, {
            height: '100%',
            ease: 'none',
            scrollTrigger: {
                trigger: wrapper,
                start: 'top 70%',
                end: 'bottom 70%',
                scrub: 0.6,
            },
        });
    });
});