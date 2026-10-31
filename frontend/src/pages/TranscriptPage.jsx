import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FileText,
  Clock,
  Search,
  Copy,
  Check,
  Download,
  ArrowLeft,
  Sparkles,
  HelpCircle,
  Loader2,
  AlertCircle
} from 'lucide-react';
import api from '../services/api';

export default function TranscriptPage() {
  const { id } = useParams();
  const [transcriptData, setTranscriptData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('segments'); // 'segments' or 'continuous'

  useEffect(() => {
    loadTranscript();
  }, [id]);

  const loadTranscript = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getLectureTranscript(id);
      setTranscriptData(res);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load lecture transcript.');
    } finally {
      setLoading(false);
    }
  };

  const formatSeconds = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const copyToClipboard = () => {
    if (!transcriptData) return;
    navigator.clipboard.writeText(transcriptData.transcript_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadTextFile = () => {
    if (!transcriptData) return;
    const element = document.createElement('a');
    const file = new Blob([transcriptData.transcript_text], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${transcriptData.title.replace(/\s+/g, '_')}_transcript.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const filteredSegments = transcriptData?.segments?.filter((seg) =>
    seg.text.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
        <p className="text-slate-400 text-sm">Fetching timestamped speech transcript...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="glass-panel p-8 rounded-2xl border border-rose-800/40 max-w-md mx-auto">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-white mb-2">Transcript Unavailable</h2>
          <p className="text-xs text-slate-400 mb-6">{error}</p>
          <div className="flex justify-center space-x-3">
            <Link
              to="/dashboard"
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
            >
              Dashboard
            </Link>
            <button
              onClick={loadTranscript}
              className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Navigation & Header */}
      <div className="mb-6">
        <Link
          to="/history"
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Lectures</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-800">
                Whisper Transcript
              </span>
              <span className="text-xs text-slate-400">
                Language: {transcriptData.detected_language.toUpperCase()}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
              {transcriptData.title}
            </h1>
          </div>

          <div className="flex items-center space-x-2">
            <Link
              to={`/lectures/${id}/summary`}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-medium transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              <span>Summary & Notes</span>
            </Link>

            <Link
              to={`/lectures/${id}/quiz`}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-colors"
            >
              <HelpCircle className="w-4 h-4" />
              <span>Take Quiz</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search words in transcript..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        {/* View toggle & Export tools */}
        <div className="flex items-center space-x-2 self-end sm:self-auto">
          <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex items-center text-xs">
            <button
              onClick={() => setViewMode('segments')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                viewMode === 'segments'
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Timestamped
            </button>
            <button
              onClick={() => setViewMode('continuous')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                viewMode === 'continuous'
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Full Text
            </button>
          </div>

          <button
            onClick={copyToClipboard}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center space-x-1"
            title="Copy to clipboard"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={downloadTextFile}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center space-x-1"
            title="Download TXT"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Transcript Body */}
      {viewMode === 'segments' ? (
        <div className="space-y-3">
          {filteredSegments.length === 0 ? (
            <div className="glass-panel p-10 rounded-2xl border border-slate-800 text-center text-slate-400 text-sm">
              No matching transcript segments found.
            </div>
          ) : (
            filteredSegments.map((seg, idx) => (
              <div
                key={idx}
                className="glass-panel p-4 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors flex items-start space-x-4"
              >
                <div className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-purple-950/60 border border-purple-800/40 text-[11px] font-mono text-purple-300 flex-shrink-0 mt-0.5">
                  <Clock className="w-3 h-3 text-purple-400" />
                  <span>{formatSeconds(seg.start)}</span>
                  <span className="text-purple-500">-</span>
                  <span>{formatSeconds(seg.end)}</span>
                </div>
                <p className="text-sm text-slate-200 leading-relaxed font-normal">
                  {seg.text}
                </p>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 leading-relaxed text-sm text-slate-300 whitespace-pre-line font-sans">
          {transcriptData.transcript_text}
        </div>
      )}
    </div>
  );
}
