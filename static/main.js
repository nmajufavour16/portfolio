document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    const themeColor = document.querySelector('meta[name="theme-color"]');
    const themeToggle = document.querySelector('[data-theme-toggle]');

    const applyTheme = (theme, persist = false) => {
        root.dataset.theme = theme;
        root.style.colorScheme = theme;
        if (themeColor) themeColor.content = theme === 'light' ? '#ffffff' : '#0f0f0f';
        if (themeToggle) {
            const nextTheme = theme === 'light' ? 'dark' : 'light';
            themeToggle.setAttribute('aria-label', `Switch to ${nextTheme} mode`);
        }
        if (persist) {
            try {
                localStorage.setItem('phayvo-theme', theme);
            } catch (error) {
                // The theme still works for this visit when storage is unavailable.
            }
        }
    };

    const playThemeClick = () => {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;

        try {
            const audio = new AudioContext();
            const oscillator = audio.createOscillator();
            const gain = audio.createGain();
            const now = audio.currentTime;

            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(620, now);
            oscillator.frequency.exponentialRampToValueAtTime(320, now + 0.045);
            gain.gain.setValueAtTime(0.035, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.055);

            oscillator.connect(gain);
            gain.connect(audio.destination);
            oscillator.start(now);
            oscillator.stop(now + 0.06);
            oscillator.addEventListener('ended', () => audio.close());
        } catch (error) {
            // Theme switching remains available when browser audio is blocked.
        }
    };

    applyTheme(root.dataset.theme === 'light' ? 'light' : 'dark');
    themeToggle?.addEventListener('click', () => {
        playThemeClick();
        applyTheme(root.dataset.theme === 'light' ? 'dark' : 'light', true);
    });

    const techVerb = document.querySelector('[data-tech-verb]');
    if (techVerb) {
        const verbs = ['engineer', 'deploy', 'design', 'orchestrate'];
        let verbIndex = 0;
        window.setInterval(() => {
            techVerb.classList.add('is-changing');
            window.setTimeout(() => {
                verbIndex = (verbIndex + 1) % verbs.length;
                techVerb.textContent = verbs[verbIndex];
                techVerb.classList.remove('is-changing');
            }, 180);
        }, 2400);
    }

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

    // Fluid contrast orb: lerps behind the pointer and stretches in the
    // direction of travel. It stays compositor-friendly and is disabled for
    // touch and reduced-motion users.
    const hero = document.querySelector('.hero');
    const heroLens = document.querySelector('[data-hero-lens]');
    const canUseLens = window.matchMedia('(hover: hover) and (pointer: fine)').matches
        && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (hero && heroLens && canUseLens) {
        let frame = null;
        let targetX = hero.clientWidth / 2;
        let targetY = hero.clientHeight / 2;
        let currentX = targetX;
        let currentY = targetY;
        let active = false;

        const animateFluidCursor = () => {
            const deltaX = targetX - currentX;
            const deltaY = targetY - currentY;
            currentX += deltaX * 0.13;
            currentY += deltaY * 0.13;

            const speed = Math.min(Math.hypot(deltaX, deltaY), 55);
            const angle = Math.max(-9, Math.min(9, deltaX * 0.16));
            const stretch = 1 + speed * 0.0045;
            const squash = Math.max(0.84, 1 - speed * 0.0025);

            heroLens.style.setProperty('--lens-x', `${currentX}px`);
            heroLens.style.setProperty('--lens-y', `${currentY}px`);
            heroLens.style.setProperty('--fluid-angle', `${angle}deg`);
            heroLens.style.setProperty('--fluid-stretch', stretch.toFixed(3));
            heroLens.style.setProperty('--fluid-squash', squash.toFixed(3));

            if (active || Math.abs(deltaX) > 0.1 || Math.abs(deltaY) > 0.1) {
                frame = requestAnimationFrame(animateFluidCursor);
            } else {
                frame = null;
            }
        };

        hero.addEventListener('pointerenter', (event) => {
            const bounds = hero.getBoundingClientRect();
            targetX = event.clientX - bounds.left;
            targetY = event.clientY - bounds.top;
            currentX = targetX;
            currentY = targetY;
            active = true;
            hero.dataset.cursorActive = 'true';
            if (!frame) frame = requestAnimationFrame(animateFluidCursor);
        });

        hero.addEventListener('pointermove', (event) => {
            const bounds = hero.getBoundingClientRect();
            targetX = event.clientX - bounds.left;
            targetY = event.clientY - bounds.top;
            if (!frame) frame = requestAnimationFrame(animateFluidCursor);
        }, { passive: true });

        hero.addEventListener('pointerleave', () => {
            active = false;
            hero.dataset.cursorActive = 'false';
        });
    }

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
