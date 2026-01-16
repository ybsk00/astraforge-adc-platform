'use client';

import React, { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import Image from 'next/image';

export default function Interactive3DCell() {
    const ref = useRef<HTMLDivElement>(null);

    // Mouse position values
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    // Smooth spring animation for rotation
    const mouseX = useSpring(x, { stiffness: 150, damping: 15 });
    const mouseY = useSpring(y, { stiffness: 150, damping: 15 });

    // Transform mouse position to rotation degrees
    // Rotate X based on Y axis movement (tilt up/down)
    const rotateX = useTransform(mouseY, [-0.5, 0.5], [15, -15]);
    // Rotate Y based on X axis movement (tilt left/right)
    const rotateY = useTransform(mouseX, [-0.5, 0.5], [-15, 15]);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;

        const rect = ref.current.getBoundingClientRect();

        // Calculate normalized position (-0.5 to 0.5)
        const width = rect.width;
        const height = rect.height;

        const mouseXFromCenter = e.clientX - rect.left - width / 2;
        const mouseYFromCenter = e.clientY - rect.top - height / 2;

        const xPct = mouseXFromCenter / width;
        const yPct = mouseYFromCenter / height;

        x.set(xPct);
        y.set(yPct);
    };

    const handleMouseLeave = () => {
        x.set(0);
        y.set(0);
    };

    return (
        <div className="relative w-full h-full flex items-center justify-center perspective-1000">
            <motion.div
                ref={ref}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
                style={{
                    rotateX,
                    rotateY,
                    transformStyle: 'preserve-3d',
                }}
                className="relative w-[500px] h-[500px] cursor-pointer"
            >
                {/* Glow Effect behind the cell */}
                <div
                    className="absolute inset-0 bg-blue-500/20 rounded-full blur-[100px] -z-10"
                    style={{ transform: 'translateZ(-50px)' }}
                />

                {/* 3D Cell Image */}
                <motion.div
                    style={{ transform: 'translateZ(50px)' }}
                    className="relative w-full h-full drop-shadow-2xl"
                >
                    <Image
                        src="/images/cancer-cell.png"
                        alt="3D Cancer Cell Visualization"
                        fill
                        className="object-contain"
                        priority
                    />

                    {/* Floating Particles (Simulated) */}
                    <div className="absolute inset-0 pointer-events-none">
                        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-blue-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
                        <div className="absolute bottom-1/3 right-1/4 w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse delay-700 shadow-[0_0_10px_rgba(168,85,247,0.8)]" />
                        <div className="absolute top-1/3 right-1/3 w-1 h-1 bg-white rounded-full animate-ping delay-1000" />
                    </div>
                </motion.div>

                {/* Status Overlay (Floating in front) */}
                <motion.div
                    style={{ transform: 'translateZ(80px)' }}
                    className="absolute bottom-0 left-1/2 -translate-x-1/2 bg-slate-900/80 backdrop-blur-md border border-white/10 rounded-xl p-4 flex items-center gap-4 w-max shadow-xl"
                >
                    <div className="relative">
                        <div className="w-3 h-3 bg-red-500 rounded-full animate-ping absolute inset-0 opacity-75"></div>
                        <div className="w-3 h-3 bg-red-500 rounded-full relative"></div>
                    </div>
                    <div>
                        <div className="text-white font-medium text-sm">Target Detected</div>
                        <div className="text-xs text-red-400 font-mono">HER2 Positive (3+)</div>
                    </div>
                </motion.div>
            </motion.div>
        </div>
    );
}
