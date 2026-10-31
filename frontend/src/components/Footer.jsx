import React from 'react';
import { Cpu, Terminal, BookOpen } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-[#080c14] py-8 text-slate-400 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 text-slate-300">
          <BookOpen className="w-4 h-4 text-purple-400" />
          <span className="font-semibold text-white">LectureAI</span>
          <span>— Final-Year B.Tech CSE Capstone Project</span>
        </div>

        <div className="flex items-center space-x-6 text-xs text-slate-500">
          <div className="flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span>faster-whisper + BART/T5</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Terminal className="w-3.5 h-3.5 text-emerald-400" />
            <span>FastAPI + PyTorch CPU/CUDA</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
