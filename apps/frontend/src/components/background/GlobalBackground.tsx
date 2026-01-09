'use client';

import { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

export default function GlobalBackground() {
    const [isMobile, setIsMobile] = useState(false);
    const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

    // Mouse position
    const mouseX = useMotionValue(0.5);
    const mouseY = useMotionValue(0.5);

    // Smooth spring animation
    const springX = useSpring(mouseX, { stiffness: 50, damping: 30 });
    const springY = useSpring(mouseY, { stiffness: 50, damping: 30 });

    // Transform to subtle parallax offset
    const blob1X = useTransform(springX, [0, 1], [-30, 30]);
    const blob1Y = useTransform(springY, [0, 1], [-20, 20]);
    const blob2X = useTransform(springX, [0, 1], [20, -20]);
    const blob2Y = useTransform(springY, [0, 1], [15, -15]);
    const blob3X = useTransform(springX, [0, 1], [-15, 15]);
    const blob3Y = useTransform(springY, [0, 1], [-25, 25]);

    useEffect(() => {
        // Check for mobile
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);

        // Check for reduced motion preference
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        setPrefersReducedMotion(mediaQuery.matches);
        mediaQuery.addEventListener('change', (e) => setPrefersReducedMotion(e.matches));

        // Mouse move handler
        const handleMouseMove = (e: MouseEvent) => {
            if (isMobile || prefersReducedMotion) return;
            mouseX.set(e.clientX / window.innerWidth);
            mouseY.set(e.clientY / window.innerHeight);
        };

        window.addEventListener('mousemove', handleMouseMove);

        return () => {
            window.removeEventListener('resize', checkMobile);
            window.removeEventListener('mousemove', handleMouseMove);
        };
    }, [isMobile, prefersReducedMotion, mouseX, mouseY]);

    // Fallback for reduced motion
    if (prefersReducedMotion) {
        return (
            <div className="fixed inset-0 -z-10 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pointer-events-none" />
        );
    }

    return (
        <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
            {/* Base gradient */}
            <div className="absolute inset-0 bg-slate-950" />

            {/* Organic Blob Layer - Cell-like shapes with inline styles for radial gradients */}
            <motion.div
                style={{
                    x: isMobile ? 0 : blob1X,
                    y: isMobile ? 0 : blob1Y,
                    background: 'radial-gradient(circle, rgba(59, 130, 246, 0.5) 0%, rgba(37, 99, 235, 0.3) 40%, transparent 70%)'
                }}
                className="absolute -top-1/4 -left-1/4 w-[600px] h-[600px] rounded-full blur-3xl animate-pulse"
            />

            <motion.div
                style={{
                    x: isMobile ? 0 : blob2X,
                    y: isMobile ? 0 : blob2Y,
                    background: 'radial-gradient(circle, rgba(168, 85, 247, 0.45) 0%, rgba(126, 34, 206, 0.25) 40%, transparent 70%)'
                }}
                className="absolute top-1/3 -right-1/4 w-[500px] h-[500px] rounded-full blur-3xl animate-pulse"
                // @ts-ignore
                style={{ animationDelay: '2s' }}
            />

            <motion.div
                style={{
                    x: isMobile ? 0 : blob3X,
                    y: isMobile ? 0 : blob3Y,
                    background: 'radial-gradient(circle, rgba(34, 211, 238, 0.4) 0%, rgba(8, 145, 178, 0.2) 40%, transparent 70%)'
                }}
                className="absolute -bottom-1/4 left-1/3 w-[700px] h-[700px] rounded-full blur-3xl animate-pulse"
                // @ts-ignore
                style={{ animationDelay: '4s' }}
            />

            {/* Particle Field Layer */}
            <div className="absolute inset-0">
                {!isMobile && [...Array(25)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute w-1.5 h-1.5 bg-blue-400/60 rounded-full shadow-[0_0_10px_rgba(96,165,250,0.5)]"
                        style={{
                            left: `${10 + (i * 6) % 80}%`,
                            top: `${15 + (i * 7) % 70}%`,
                        }}
                        animate={{
                            y: [0, -30, 0],
                            opacity: [0.4, 0.8, 0.4],
                        }}
                        transition={{
                            duration: 4 + (i % 4),
                            repeat: Infinity,
                            delay: i * 0.5,
                            ease: 'easeInOut',
                        }}
                    />
                ))}
            </div>

            {/* Fog overlay - Reduced opacity */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-950/10 to-slate-950/30" />
        </div>
    );
}
