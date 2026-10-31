import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Upload,
  FileVideo,
  FileAudio,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  Sparkles,
  Info,
  X
} from 'lucide-react';
import api from '../services/api';

const SUPPORTED_EXTS = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg'];
const MAX_FILE_SIZE_MB = 250;

export default function UploadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const monitorId = searchParams.get('monitor');

  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [lectureTitle, setLectureTitle] = useState('');
  const [language, setLanguage] = useState('auto');
  const [isDragging, setIsDragging] = useState(false);

  // Upload & processing states
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeLectureId, setActiveLectureId] = useState(monitorId ? parseInt(monitorId) : null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Status Polling
  useEffect(() => {
    if (!activeLectureId) return;

    let isSubscribed = true;
    const pollInterval = setInterval(async () => {
      try {
        const res = await api.getLectureStatus(activeLectureId);
        if (!isSubscribed) return;
        setProcessingStatus(res);

        if (res.status === 'completed' || res.status === 'failed') {
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Status check error:', err);
      }
    }, 2500);

    return () => {
      isSubscribed = false;
      clearInterval(pollInterval);
    };
  }, [activeLectureId]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const validateAndSetFile = (file) => {
    setErrorMessage(null);
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!SUPPORTED_EXTS.includes(ext)) {
      setErrorMessage(`Format '${ext}' is not supported. Please upload MP4, WebM, MP3, WAV, etc.`);
      return;
    }

    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > MAX_FILE_SIZE_MB) {
      setErrorMessage(`File size (${sizeMb.toFixed(1)}MB) exceeds maximum ${MAX_FILE_SIZE_MB}MB limit.`);
      return;
    }

    setSelectedFile(file);
    if (!lectureTitle) {
      const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
      setLectureTitle(cleanName);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select a video or audio file first.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (lectureTitle.trim()) {
      formData.append('title', lectureTitle.trim());
    }
    formData.append('language', language);

    try {
      const res = await api.uploadLecture(formData, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        }
      });

      setActiveLectureId(res.id);
      setIsUploading(false);
    } catch (err) {
      setIsUploading(false);
      setErrorMessage(
        err.response?.data?.detail || 'Failed to upload lecture file. Ensure backend is running.'
      );
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setLectureTitle('');
    setActiveLectureId(null);
    setProcessingStatus(null);
    setErrorMessage(null);
    setUploadProgress(0);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16">
      {/* Title */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Upload Lecture Media</h1>
        <p className="text-slate-400 text-sm mt-2 max-w-xl mx-auto">
          Upload recorded lectures in video (MP4, WebM, MKV) or audio (MP3, WAV, M4A) format
          to automatically run speech recognition, summarization, and quiz synthesis.
        </p>
      </div>

      {errorMessage && (
        <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Upload Error: </span>
            {errorMessage}
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Processing Monitor View */}
      {activeLectureId ? (
        <div className="glass-panel p-8 rounded-2xl border border-slate-800">
          <div className="text-center mb-6">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
              AI Processing Pipeline
            </span>
            <h2 className="text-xl font-bold text-white mt-1">
              {processingStatus?.title || lectureTitle || 'Processing Lecture'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Lecture ID #{activeLectureId} • {processingStatus?.detected_language?.toUpperCase() || 'EN'}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2 mb-8">
            <div className="flex justify-between text-xs text-slate-300 font-medium">
              <span>{processingStatus?.status_message || 'Initializing AI pipeline...'}</span>
              <span>{processingStatus?.progress_percent || 0}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-purple-600 via-indigo-500 to-sky-400 h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${processingStatus?.progress_percent || 5}%` }}
              />
            </div>
          </div>

          {/* Step Indicators */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <div className={`p-3 rounded-xl border text-center text-xs ${
              (processingStatus?.progress_percent || 0) >= 15
                ? 'bg-purple-950/40 border-purple-800/60 text-purple-300'
                : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}>
              <div className="font-semibold mb-1">1. Audio Extract</div>
              <div>FFmpeg 16kHz</div>
            </div>

            <div className={`p-3 rounded-xl border text-center text-xs ${
              (processingStatus?.progress_percent || 0) >= 35
                ? 'bg-purple-950/40 border-purple-800/60 text-purple-300'
                : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}>
              <div className="font-semibold mb-1">2. Transcription</div>
              <div>faster-whisper</div>
            </div>

            <div className={`p-3 rounded-xl border text-center text-xs ${
              (processingStatus?.progress_percent || 0) >= 65
                ? 'bg-purple-950/40 border-purple-800/60 text-purple-300'
                : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}>
              <div className="font-semibold mb-1">3. Summarization</div>
              <div>BART / FLAN-T5</div>
            </div>

            <div className={`p-3 rounded-xl border text-center text-xs ${
              (processingStatus?.progress_percent || 0) >= 100
                ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}>
              <div className="font-semibold mb-1">4. Grounded MCQs</div>
              <div>Quiz Ready</div>
            </div>
          </div>

          {/* Completion Actions */}
          {processingStatus?.status === 'completed' && (
            <div className="space-y-4 pt-2">
              <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-sm flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                <span>All deep learning stages finished successfully!</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Link
                  to={`/lectures/${activeLectureId}/summary`}
                  className="flex items-center justify-center space-x-2 px-4 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm transition-colors text-center"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>View Notes & Summary</span>
                </Link>

                <Link
                  to={`/lectures/${activeLectureId}/quiz`}
                  className="flex items-center justify-center space-x-2 px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors text-center"
                >
                  <span>Practice Quiz</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <Link
                  to={`/lectures/${activeLectureId}/transcript`}
                  className="flex items-center justify-center space-x-2 px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-colors text-center"
                >
                  <span>Transcript</span>
                </Link>
              </div>

              <div className="text-center pt-4">
                <button
                  onClick={resetForm}
                  className="text-xs text-slate-400 hover:text-slate-200 underline"
                >
                  Upload another lecture
                </button>
              </div>
            </div>
          )}

          {/* Failed State */}
          {processingStatus?.status === 'failed' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-sm">
                <div className="font-semibold mb-1">Processing Failed:</div>
                <p className="text-xs text-rose-200">{processingStatus.error_message || 'An unknown error occurred during inference.'}</p>
              </div>
              <button
                onClick={resetForm}
                className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Ongoing State */}
          {processingStatus?.status !== 'completed' && processingStatus?.status !== 'failed' && (
            <div className="flex items-center justify-center space-x-2 text-slate-400 text-xs py-4">
              <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
              <span>Inference executing in background. You may navigate away safely.</span>
            </div>
          )}
        </div>
      ) : (
        /* Upload Form */
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Drag & Drop Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-purple-500 bg-purple-950/20'
                : selectedFile
                ? 'border-purple-600/60 bg-purple-950/10'
                : 'border-slate-700 hover:border-slate-500 bg-slate-900/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept={SUPPORTED_EXTS.join(',')}
              className="hidden"
            />

            {selectedFile ? (
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-2xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400 mb-3">
                  {selectedFile.type.startsWith('video') ? (
                    <FileVideo className="w-7 h-7" />
                  ) : (
                    <FileAudio className="w-7 h-7" />
                  )}
                </div>
                <p className="text-sm font-bold text-white mb-1 truncate max-w-sm">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-400">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to upload
                </p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                  className="mt-3 text-xs text-purple-400 hover:text-purple-300 font-medium"
                >
                  Change file
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 mb-4">
                  <Upload className="w-6 h-6 text-purple-400" />
                </div>
                <p className="text-sm font-semibold text-white mb-1">
                  Click to select or drag & drop lecture file here
                </p>
                <p className="text-xs text-slate-400 max-w-xs mb-3">
                  MP4, WebM, MKV, MP3, WAV, M4A, AAC (up to {MAX_FILE_SIZE_MB}MB)
                </p>
                <span className="text-[11px] text-purple-400 bg-purple-950/40 px-3 py-1 rounded-full border border-purple-800/40">
                  Audio will be extracted automatically via FFmpeg
                </span>
              </div>
            )}
          </div>

          {/* Form Options */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Lecture Title (Optional)
              </label>
              <input
                type="text"
                value={lectureTitle}
                onChange={(e) => setLectureTitle(e.target.value)}
                placeholder="e.g. CS601 - Introduction to Deep Neural Networks"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Lecture Spoken Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 text-white text-sm focus:outline-none focus:border-purple-500"
                >
                  <option value="auto">Automatic Detection (Recommended)</option>
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="hi">Hindi</option>
                  <option value="zh">Chinese</option>
                  <option value="ja">Japanese</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  AI Model Configuration
                </label>
                <div className="px-4 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 text-xs text-slate-300 flex items-center space-x-2">
                  <Info className="w-4 h-4 text-purple-400 flex-shrink-0" />
                  <span>Whisper (base) + BART-CNN Summarizer</span>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Progress Bar */}
          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-300">
                <span>Uploading lecture to server...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-purple-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!selectedFile || isUploading}
            className={`w-full py-4 rounded-xl font-bold text-sm shadow-lg transition-all flex items-center justify-center space-x-2 ${
              !selectedFile || isUploading
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-purple-500/25 hover:from-purple-500 hover:to-indigo-500 hover:scale-[1.01]'
            }`}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Uploading... ({uploadProgress}%)</span>
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                <span>Upload & Start AI Processing</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}
