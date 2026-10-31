import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  FileText,
  Sparkles,
  HelpCircle,
  Trash2,
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Upload,
  Clock,
  Filter
} from 'lucide-react';
import api from '../services/api';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getHistory();
      setHistory(res.lectures || []);
    } catch (err) {
      setError('Could not connect to backend to retrieve lecture history.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (lectureId) => {
    if (!window.confirm('Are you sure you want to delete this lecture, its transcript, and quiz attempts?')) {
      return;
    }

    try {
      setDeletingId(lectureId);
      await api.deleteLecture(lectureId);
      setHistory((prev) => prev.filter((item) => item.id !== lectureId));
    } catch (err) {
      alert('Failed to delete lecture: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDeletingId(null);
    }
  };

  const filteredLectures = history.filter((item) => {
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.original_filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="w-3 h-3" />
            <span>Ready</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-800/60">
            <AlertCircle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-300 border border-indigo-700/60 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span className="capitalize">{status}</span>
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
        <p className="text-slate-400 text-sm">Loading lecture library...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Lecture Library & History
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Access past transcripts, summaries, and self-assessment quizzes anytime.
          </p>
        </div>

        <Link
          to="/upload"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-sm shadow-lg shadow-purple-500/20 transition-all self-start sm:self-auto"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Lecture</span>
        </Link>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadHistory} className="underline hover:text-white font-medium">Retry</button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title or filename..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="transcribing">Transcribing</option>
            <option value="summarizing">Summarizing</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Lectures List */}
      {filteredLectures.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center">
          <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No lectures found</h3>
          <p className="text-xs text-slate-400 mt-1 mb-6">
            {searchQuery ? 'Try clearing your search query.' : 'Upload a lecture video or audio file to get started.'}
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs"
          >
            <Upload className="w-4 h-4" />
            <span>Upload New Lecture</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredLectures.map((lec) => (
            <div
              key={lec.id}
              className="glass-panel p-5 rounded-2xl border border-slate-800 glow-card flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="flex items-start space-x-3.5 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-purple-400 flex-shrink-0 mt-0.5">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                    <h3 className="text-sm font-bold text-white truncate max-w-md">{lec.title}</h3>
                    {getStatusBadge(lec.status)}
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1.5 flex-wrap gap-y-1">
                    <span>{lec.original_filename}</span>
                    <span>•</span>
                    <span className="uppercase">{lec.file_type}</span>
                    <span>•</span>
                    <span>{lec.duration_seconds > 0 ? `${Math.round(lec.duration_seconds / 60)} mins` : `${lec.file_size_mb} MB`}</span>
                    <span>•</span>
                    <span>{new Date(lec.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 flex-wrap gap-y-2 self-end md:self-center">
                {lec.status === 'completed' && (
                  <>
                    <Link
                      to={`/lectures/${lec.id}/transcript`}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                    >
                      Transcript
                    </Link>

                    <Link
                      to={`/lectures/${lec.id}/summary`}
                      className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 text-xs font-medium border border-purple-500/30 transition-colors"
                    >
                      Summary & Notes
                    </Link>

                    <Link
                      to={`/lectures/${lec.id}/quiz`}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-medium border border-indigo-500/30 transition-colors"
                    >
                      Quiz
                    </Link>
                  </>
                )}

                {lec.status !== 'completed' && lec.status !== 'failed' && (
                  <Link
                    to={`/upload?monitor=${lec.id}`}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-medium"
                  >
                    Monitor Status
                  </Link>
                )}

                <button
                  onClick={() => handleDelete(lec.id)}
                  disabled={deletingId === lec.id}
                  className="p-2 rounded-lg bg-slate-800/80 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition-colors border border-transparent hover:border-rose-900/50"
                  title="Delete Lecture"
                >
                  {deletingId === lec.id ? (
                    <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
