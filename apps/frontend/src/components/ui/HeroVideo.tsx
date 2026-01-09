'use client';

export default function HeroVideo() {
    return (
        <div className="relative w-full h-full flex items-center justify-center">
            {/* Video Container */}
            <div className="relative w-[500px] h-[500px] rounded-2xl overflow-hidden shadow-2xl">
                {/* Glow Effect */}
                <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-[100px] -z-10" />

                {/* Video */}
                <video
                    autoPlay
                    loop
                    muted
                    playsInline
                    className="w-full h-full object-cover"
                    poster="/images/cancer-cell.png"
                >
                    <source src="/videos/hero-cell.mp4" type="video/mp4" />
                </video>

                {/* Status Overlay */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-slate-900/80 backdrop-blur-md border border-white/10 rounded-xl p-4 flex items-center gap-4 w-max shadow-xl">
                    <div className="relative">
                        <div className="w-3 h-3 bg-red-500 rounded-full animate-ping absolute inset-0 opacity-75"></div>
                        <div className="w-3 h-3 bg-red-500 rounded-full relative"></div>
                    </div>
                    <div>
                        <div className="text-white font-medium text-sm">Target Detected</div>
                        <div className="text-xs text-red-400 font-mono">HER2 Positive (3+)</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
