import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Award,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowLeft,
  RefreshCw,
  FileText,
  Loader2,
  AlertCircle,
  Quote
} from 'lucide-react';
import api from '../services/api';

export default function ResultsPage() {
  const { id, attemptId } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAttemptResults();
  }, [id, attemptId]);

  const loadAttemptResults = async () => {
    try {
      setLoading(true);
      setError(null);
      // Retrieve latest quiz for quiz_id or attempt directly
      const quizInfo = await api.getLatestQuiz(id);
      const res = await api.getQuizAttempt(quizInfo.quiz_id, attemptId);
      setResult(res);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load quiz evaluation results.');
    } finally {
      setLoading(false);
    }
  };

  const formatSeconds = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
        <p className="text-slate-400 text-sm">Grading answers and generating score report...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="glass-panel p-8 rounded-2xl border border-rose-800/40 max-w-md mx-auto">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-white mb-2">Evaluation Not Found</h2>
          <p className="text-xs text-slate-400 mb-6">{error || 'Could not locate quiz evaluation.'}</p>
          <Link
            to={`/lectures/${id}/quiz`}
            className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-semibold"
          >
            Go to Quiz
          </Link>
        </div>
      </div>
    );
  }

  const isPassed = result.score_percentage >= 70;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Top Breadcrumb */}
      <div className="mb-6">
        <Link
          to={`/lectures/${id}/quiz`}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Quiz</span>
        </Link>
      </div>

      {/* Main Score Card Banner */}
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center mb-8 relative overflow-hidden">
        <div className="w-16 h-16 rounded-2xl bg-purple-950/70 border border-purple-800/60 flex items-center justify-center text-purple-400 mx-auto mb-4">
          <Award className="w-8 h-8" />
        </div>

        <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
          Quiz Evaluation Report
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-1 mb-2">
          {result.lecture_title}
        </h1>

        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full text-sm font-bold my-4 border ${
          isPassed
            ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
            : 'bg-amber-950/80 text-amber-300 border-amber-800'
        }">
          <span>{result.score_percentage}% Score</span>
          <span>•</span>
          <span>{result.correct_answers} of {result.total_questions} Correct</span>
        </div>

        <div className="flex items-center justify-center space-x-6 text-xs text-slate-400 mt-2">
          <div className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-purple-400" />
            <span>Time Taken: {formatSeconds(result.time_taken_seconds)}</span>
          </div>
          <span>•</span>
          <span>Completed: {new Date(result.completed_at).toLocaleTimeString()}</span>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-8">
          <Link
            to={`/lectures/${id}/quiz`}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retake Quiz</span>
          </Link>

          <Link
            to={`/lectures/${id}/summary`}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-colors"
          >
            <FileText className="w-4 h-4 text-purple-400" />
            <span>Review Study Notes</span>
          </Link>
        </div>
      </div>

      {/* Detailed Question Review */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white mb-2">Question-by-Question Analysis</h2>

        {result.evaluations.map((evalItem, idx) => {
          const isCorrect = evalItem.is_correct;
          return (
            <div
              key={idx}
              className={`glass-panel p-6 rounded-2xl border transition-all ${
                isCorrect ? 'border-emerald-900/40 bg-emerald-950/10' : 'border-rose-900/40 bg-rose-950/10'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Question {idx + 1}
                </span>
                {isCorrect ? (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Correct (+1)</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Incorrect (0)</span>
                  </span>
                )}
              </div>

              <h3 className="text-base font-bold text-white mb-4 leading-relaxed">
                {evalItem.question}
              </h3>

              {/* Answers Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                <div className={`p-3.5 rounded-xl border text-xs ${
                  isCorrect
                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-200'
                    : 'bg-rose-950/30 border-rose-800/60 text-rose-200'
                }`}>
                  <div className="font-semibold text-slate-400 mb-1">Your Answer:</div>
                  <div className="font-medium">{evalItem.user_answer || 'Not answered'}</div>
                </div>

                {!isCorrect && (
                  <div className="p-3.5 rounded-xl border bg-emerald-950/30 border-emerald-800/60 text-emerald-200 text-xs">
                    <div className="font-semibold text-slate-400 mb-1">Correct Answer:</div>
                    <div className="font-medium">{evalItem.correct_answer}</div>
                  </div>
                )}
              </div>

              {/* Explanation & Lecture Context */}
              <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                <div className="text-slate-300 leading-relaxed">
                  <span className="font-semibold text-purple-400">Explanation: </span>
                  {evalItem.explanation}
                </div>

                {evalItem.context_source && (
                  <div className="pt-2 border-t border-slate-800 text-slate-400 flex items-start space-x-2 italic">
                    <Quote className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
                    <span>Reference quote: "{evalItem.context_source}"</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
