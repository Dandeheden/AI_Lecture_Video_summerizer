import React from 'react';
import { Link } from 'react-router-dom';
import {
  Upload,
  FileText,
  Sparkles,
  HelpCircle,
  BarChart3,
  Clock,
  CheckCircle2,
  Cpu,
  ArrowRight
} from 'lucide-react';

export default function LandingPage() {
  const features = [
    {
      icon: Cpu,
      title: 'Speech Recognition',
      desc: 'Powered by faster-whisper. Converts raw lecture audio or video into precise, timestamped transcripts with multi-language support.',
      tag: 'Whisper Seq2Seq',
    },
    {
      icon: Sparkles,
      title: 'Transformer Summaries',
      desc: 'Chunk-aware Seq2Seq Transformer pipelines (BART / FLAN-T5) generate concise summaries without losing vital academic nuances.',
      tag: 'BART / FLAN-T5',
    },
    {
      icon: FileText,
      title: 'Structured Study Guides',
      desc: 'Automatically extracts key terminology definitions, pedagogical takeaways, bulleted revision points, and exam prep tips.',
      tag: 'Automated Notes',
    },
    {
      icon: HelpCircle,
      title: 'Automatic MCQ Generator',
      desc: 'Synthesizes 4-option multiple-choice questions grounded in actual lecture content with verified answers and explanations.',
      tag: 'Grounded QG',
    },
    {
      icon: BarChart3,
      title: 'Interactive Quiz & Scoring',
      desc: 'Take timed practice quizzes with server-side validation, instant percentage scoring, and detailed answer explanations.',
      tag: 'Practice Engine',
    },
    {
      icon: Clock,
      title: 'Persistent Lecture History',
      desc: 'All transcripts, summaries, and prior quiz attempts are permanently stored in SQLite for instant revision anytime.',
      tag: 'Local Persistence',
    },
  ];

  return (
    <div className="py-12 sm:py-16">
      {/* Hero Section */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-purple-900/40 border border-purple-500/30 text-purple-300 text-xs font-semibold mb-8 backdrop-blur-sm">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Final-Year B.Tech CSE Project • Deep Learning & NLP</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight mb-6">
          AI-Powered Lecture Video{' '}
          <span className="bg-gradient-to-r from-purple-400 via-indigo-300 to-sky-400 bg-clip-text text-transparent">
            Summarizer & Quiz Generator
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto mb-10 leading-relaxed">
          Transform lengthy lecture recordings into clean timestamped transcripts,
          coherent summaries, structured study notes, and self-assessment quizzes using real deep learning models.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/upload"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold text-base shadow-lg shadow-purple-500/25 hover:from-purple-500 hover:to-indigo-500 transition-all hover:scale-[1.02]"
          >
            <Upload className="w-5 h-5" />
            <span>Upload Lecture</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>

          <Link
            to="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-4 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 font-semibold text-base border border-slate-700/80 transition-all"
          >
            <span>View Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-24">
        <div className="text-center mb-16">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
            End-to-End Educational Intelligence Pipeline
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
            Engineered with modern transformer architectures and optimized for local laptop CPU/GPU inference.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div
                key={idx}
                className="glass-panel p-6 rounded-2xl glow-card relative overflow-hidden group border border-slate-800 hover:border-purple-500/40"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-950/60 border border-purple-800/40 flex items-center justify-center text-purple-400 group-hover:text-purple-300 transition-colors">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-purple-400/80 bg-purple-950/40 px-2.5 py-1 rounded-md border border-purple-900/50">
                    {feat.tag}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{feat.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Architecture Highlights */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-24">
        <div className="glass-panel p-8 sm:p-10 rounded-2xl border border-slate-800">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">System Design</span>
              <h3 className="text-2xl font-bold text-white mt-1 mb-3">Academic Project Architecture</h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-4">
                Full-stack decoupled architecture ensuring low latency and asynchronous model execution.
              </p>
              <div className="space-y-2.5 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>PyTorch & faster-whisper CTranslate2 runtime</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Hugging Face Seq2Seq Transformers with chunking</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>FastAPI background task queuing & SQLite persistence</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800">
                <h4 className="text-sm font-semibold text-purple-300 mb-2">1. Ingestion & Preprocessing</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Extracts 16kHz audio from videos via FFmpeg, cleans silence with Voice Activity Detection (VAD), and handles multi-format uploads safely.
                </p>
              </div>
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800">
                <h4 className="text-sm font-semibold text-indigo-300 mb-2">2. Speech Transcription</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Generates sentence-level timestamped chunks with automatic language detection, streaming segments to SQLite storage.
                </p>
              </div>
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800">
                <h4 className="text-sm font-semibold text-sky-300 mb-2">3. Hierarchical Summarization</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Recursive context chunking prevents token overflow in attention matrices, generating structured notes and key terms.
                </p>
              </div>
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800">
                <h4 className="text-sm font-semibold text-emerald-300 mb-2">4. Grounded Quiz Synthesis</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Extracts verified facts from transcript clauses and synthesizes 4 distinct options with server-side validation.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
