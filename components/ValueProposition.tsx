import React from 'react';

interface ValuePropositionProps {
  onDashboard: () => void;
}

export const ValueProposition: React.FC<ValuePropositionProps> = ({ onDashboard }) => {
  return (
    <section className="relative w-full min-h-[90vh] bg-dark-900 flex items-center justify-center py-24 overflow-hidden">
        {/* Background Gradients - Subtle Parallax Effect */}
        <div className="absolute top-1/4 left-0 w-full h-1/2 bg-gradient-to-r from-brand-900/10 to-transparent -skew-y-6 pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-indigo-900/10 blur-[120px] rounded-full pointer-events-none" />
        
        <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10 w-full">
            <div className="glass-panel rounded-3xl p-8 md:p-16 border border-white/5 bg-gradient-to-br from-white/5 via-white/[0.02] to-transparent relative overflow-hidden group">
                
                {/* Decorative glow inside card */}
                <div className="absolute -top-24 -right-24 w-64 h-64 bg-brand-500/20 rounded-full blur-[80px] pointer-events-none opacity-50 group-hover:opacity-100 transition-opacity duration-700" />
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    {/* Text Content */}
                    <div className="space-y-8 relative z-20">
                        <div>
                            <h2 className="text-3xl md:text-5xl font-display font-medium text-white leading-tight mb-4">
                                Shaping the future of credit, <span className="text-brand-400">responsibly.</span>
                            </h2>
                            <p className="text-xl text-slate-400 font-light font-display">
                                One model. One decision. Millions of lives impacted.
                            </p>
                        </div>
                        
                        <p className="text-slate-400 leading-relaxed max-w-md text-base border-l border-white/10 pl-4">
                            CreditSmart combines explainable AI, risk scoring, and regulatory-aware modeling to help lenders make decisions that are fair, fast, and transparent.
                        </p>

                        <button 
                            onClick={onDashboard}
                            className="group flex items-center gap-3 text-white font-medium border-b border-brand-500/50 pb-1 hover:border-brand-500 transition-all hover:pl-2 w-fit"
                        >
                            View Risk Dashboard
                            <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                            </svg>
                        </button>
                    </div>

                    {/* Visual Abstraction */}
                    <div className="relative h-[450px] w-full flex items-center justify-center perspective-[1000px]">
                        
                        {/* Connecting Lines (SVG) */}
                         <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20" style={{ zIndex: 0 }}>
                            <path d="M150 225 Q 250 150 350 100" stroke="url(#lineGradient)" strokeWidth="1" fill="none" strokeDasharray="4 4" className="animate-pulse" />
                            <path d="M150 225 Q 200 350 150 380" stroke="url(#lineGradient)" strokeWidth="1" fill="none" strokeDasharray="4 4" className="animate-pulse" style={{ animationDelay: '1s' }} />
                            <defs>
                                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0" />
                                    <stop offset="50%" stopColor="#38bdf8" stopOpacity="1" />
                                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
                                </linearGradient>
                            </defs>
                        </svg>

                        {/* Central Node */}
                        <div className="relative z-10 w-24 h-24 rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 shadow-[0_0_50px_rgba(56,189,248,0.3)] flex items-center justify-center transform transition-transform duration-700 hover:scale-110 border border-white/20">
                            <div className="absolute inset-0 bg-noise opacity-20 mix-blend-overlay"></div>
                            <svg className="w-10 h-10 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                        </div>

                        {/* Orbiting Cards */}
                        {/* Card 1: Risk */}
                        <div className="absolute top-12 right-10 md:right-16 p-4 rounded-xl glass-panel border-white/10 bg-dark-900/60 backdrop-blur-md shadow-xl animate-float" style={{animationDelay: '0s'}}>
                            <div className="flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]"></div>
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Analysis</div>
                                    <div className="text-xs font-mono text-slate-200">Risk: Low</div>
                                </div>
                            </div>
                        </div>

                        {/* Card 2: Probability */}
                        <div className="absolute bottom-20 left-4 md:left-12 p-4 rounded-xl glass-panel border-white/10 bg-dark-900/60 backdrop-blur-md shadow-xl animate-float" style={{animationDelay: '2s'}}>
                            <div className="flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Confidence</div>
                                    <div className="text-xs font-mono text-slate-200">Probability: 98.4%</div>
                                </div>
                            </div>
                        </div>

                        {/* Card 3: Explainability */}
                        <div className="absolute top-1/2 left-0 -translate-y-1/2 -translate-x-2 md:-translate-x-6 p-4 rounded-xl glass-panel border-white/10 bg-dark-900/60 backdrop-blur-md shadow-xl animate-float" style={{animationDelay: '3.5s'}}>
                            <div className="flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-brand-400 shadow-[0_0_10px_rgba(56,189,248,0.5)]"></div>
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Mode</div>
                                    <div className="text-xs font-mono text-slate-200">Explainable AI</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
  );
};