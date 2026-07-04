import React from 'react';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col justify-between bg-radial from-[#1e2230] to-[#0d0f12]">
      <header className="px-6 py-4 flex justify-between items-center border-b border-white/10 backdrop-blur-md bg-black/20 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#00f2fe] to-[#4facfe] flex items-center justify-center font-bold text-black shadow-[0_0_15px_rgba(0,242,254,0.4)]">
            M
          </div>
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-500 bg-clip-text text-transparent">
            Mediva Healthcare
          </span>
        </div>
        <nav className="hidden md:flex gap-6 text-sm text-gray-400">
          <a href="#" className="hover:text-white transition-colors">Dashboard</a>
          <a href="#" className="hover:text-white transition-colors">Consultations</a>
          <a href="#" className="hover:text-white transition-colors">Vitals Monitor</a>
          <a href="#" className="hover:text-white transition-colors">AI Diagnostics</a>
        </nav>
        <button className="px-4 py-2 text-xs font-semibold rounded-lg bg-white/10 text-white border border-white/10 hover:bg-white/20 transition-all">
          Connect Supabase
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-16 text-center max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-[#00f2fe] mb-8 shadow-inner">
          <span className="w-2 h-2 rounded-full bg-[#00f2fe] animate-pulse"></span>
          Mediva Architecture Standardized
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 bg-gradient-to-b from-white via-gray-100 to-gray-400 bg-clip-text text-transparent">
          Next-Generation <br />
          <span className="bg-gradient-to-r from-[#00f2fe] to-[#4facfe] bg-clip-text text-transparent">
            Remote Patient Monitoring
          </span>
        </h1>
        <p className="text-gray-400 text-lg mb-12 max-w-2xl leading-relaxed">
          A high-performance monorepo platform standardizing AI diagnostic pipelines, LiveKit video consultations, and Supabase integration.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-[#00f2fe]/40 transition-all group">
            <h3 className="font-bold text-lg mb-2 group-hover:text-[#00f2fe] transition-colors">FastAPI Backend</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Fully asynchronous service API with Alembic migrations, SQLAlchemy database models, and integrated Supabase Auth checks.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-[#00f2fe]/40 transition-all group">
            <h3 className="font-bold text-lg mb-2 group-hover:text-[#00f2fe] transition-colors">AI Services</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Standardized triage classifier, real-time vital streams anomaly detection, and automated patient report summarizers.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-[#00f2fe]/40 transition-all group">
            <h3 className="font-bold text-lg mb-2 group-hover:text-[#00f2fe] transition-colors">LiveKit & Redis</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Low latency telehealth video consulting rooms backend integrated with Celery background notification queues.
            </p>
          </div>
        </div>
      </main>

      <footer className="py-8 text-center text-xs text-gray-500 border-t border-white/5">
        &copy; {new Date().getFullYear()} Mediva Platform. All rights reserved.
      </footer>
    </div>
  );
}
