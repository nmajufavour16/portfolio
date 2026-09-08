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

    const menuToggle = document.querySelector('.site-header__toggle');
    menuToggle?.addEventListener('click', () => {
        playThemeClick();
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
    const heroCard = document.querySelector('.hero-card');
    const canUseLens = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (hero && heroCard && canUseLens) {
        // Create reverse-theme clone wrapper
        const cloneWrapper = document.createElement('div');
        cloneWrapper.className = 'hero-card-lens-wrapper';
        cloneWrapper.setAttribute('aria-hidden', 'true');

        const reverseContainer = document.createElement('div');
        reverseContainer.className = 'lens-reverse-container';
        
        const clone = heroCard.cloneNode(true);
        const glow = clone.querySelector('.nav-border-glow');
        if (glow) glow.remove();
        
        // Clear all GSAP inline styles from the clone to prevent alignment issues
        clone.removeAttribute('style');
        clone.removeAttribute('data-reveal');
        clone.querySelectorAll('[data-reveal], [style]').forEach(el => {
            el.removeAttribute('data-reveal');
            el.removeAttribute('style');
        });
        
        reverseContainer.appendChild(clone);
        cloneWrapper.appendChild(reverseContainer);
        hero.appendChild(cloneWrapper);
        
        // Remove old orb
        const oldOrb = document.querySelector('[data-hero-lens]');
        if (oldOrb) oldOrb.remove();

        const updateLensTheme = () => {
            const currentTheme = document.documentElement.dataset.theme;
            cloneWrapper.dataset.theme = currentTheme === 'light' ? 'dark' : 'light';
        };
        updateLensTheme();
        // Hook into theme toggle
        themeToggle?.addEventListener('click', () => {
            setTimeout(updateLensTheme, 10);
        });

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

            const velocity = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            const squash = Math.max(0.6, 1 - velocity * 0.004);
            const stretch = Math.min(1.4, 1 + velocity * 0.004);
            const angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI);

            cloneWrapper.style.setProperty('--lens-x', `${currentX}px`);
            cloneWrapper.style.setProperty('--lens-y', `${currentY}px`);
            cloneWrapper.style.setProperty('--fluid-angle', `${angle}deg`);
            cloneWrapper.style.setProperty('--fluid-stretch', stretch.toFixed(3));
            cloneWrapper.style.setProperty('--fluid-squash', squash.toFixed(3));
            
            cloneWrapper.style.setProperty('--inv-angle', `${-angle}deg`);
            cloneWrapper.style.setProperty('--inv-stretch', (1 / stretch).toFixed(3));
            cloneWrapper.style.setProperty('--inv-squash', (1 / squash).toFixed(3));

            cloneWrapper.style.opacity = active ? 1 : 0;

            requestAnimationFrame(animateFluidCursor);
        };

        let idleTimeout;
        hero.addEventListener('pointermove', (e) => {
            active = true;
            const rect = hero.getBoundingClientRect();
            targetX = e.clientX - rect.left;
            targetY = e.clientY - rect.top;
            
            clearTimeout(idleTimeout);
            idleTimeout = setTimeout(() => {
                active = false;
            }, 1000);
        }, { passive: true });

        hero.addEventListener('pointerleave', () => {
            active = false;
            clearTimeout(idleTimeout);
            hero.dataset.cursorActive = 'false';
        });
        
        requestAnimationFrame(animateFluidCursor);
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
