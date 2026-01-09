'use client';

import { useEffect, useRef, useState } from 'react';
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

    // Fallback for reduced motion or mobile
    if (prefersReducedMotion) {
        return (
            <div className="fixed inset-0 -z-50 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pointer-events-none" />
        );
    }

    return (
        <div className="fixed inset-0 -z-50 overflow-hidden pointer-events-none bg-slate-950">
            {/* Fog / Depth Layer */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-950/50 to-slate-950" />

            {/* Organic Blob Layer - Cell-like shapes */}
            <motion.div
                style={{ x: isMobile ? 0 : blob1X, y: isMobile ? 0 : blob1Y }}
                className="absolute -top-1/4 -left-1/4 w-[600px] h-[600px] rounded-full bg-gradient-radial from-blue-600/20 via-blue-900/10 to-transparent blur-3xl"
            >
                <div className="w-full h-full rounded-full animate-pulse" style={{ animationDuration: '8s' }} />
            </motion.div>

            <motion.div
                style={{ x: isMobile ? 0 : blob2X, y: isMobile ? 0 : blob2Y }}
                className="absolute top-1/3 -right-1/4 w-[500px] h-[500px] rounded-full bg-gradient-radial from-purple-600/15 via-purple-900/10 to-transparent blur-3xl"
            >
                <div className="w-full h-full rounded-full animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
            </motion.div>

            <motion.div
                style={{ x: isMobile ? 0 : blob3X, y: isMobile ? 0 : blob3Y }}
                className="absolute -bottom-1/4 left-1/3 w-[700px] h-[700px] rounded-full bg-gradient-radial from-cyan-600/10 via-cyan-900/5 to-transparent blur-3xl"
            >
                <div className="w-full h-full rounded-full animate-pulse" style={{ animationDuration: '12s', animationDelay: '4s' }} />
            </motion.div>

            {/* Particle Field Layer */}
            <div className="absolute inset-0">
                {!isMobile && [...Array(20)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute w-1 h-1 bg-white/20 rounded-full"
                        style={{
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                        }}
                        animate={{
                            y: [0, -30, 0],
                            opacity: [0.2, 0.5, 0.2],
                        }}
                        transition={{
                            duration: 5 + Math.random() * 5,
                            repeat: Infinity,
                            delay: Math.random() * 5,
                            ease: 'easeInOut',
                        }}
                    />
                ))}
            </div>

            {/* Top Gradient Overlay */}
            <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-slate-950 to-transparent" />

            {/* Bottom Gradient Overlay */}
            <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent" />
        </div>
    );
}
