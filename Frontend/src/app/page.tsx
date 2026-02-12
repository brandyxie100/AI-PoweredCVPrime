/**
 * Home Page — the main CV Analysis workflow.
 *
 * Flow:  Upload → Analyzing → Results
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

"use client";

import { useState } from "react";
import type { AppStep, CVUploadResponse, CVAnalysisResult } from "@/types";
import { uploadCV, analyzeCV } from "@/lib/api";
import Header from "@/components/Header";
import FileUpload from "@/components/FileUpload";
import LoadingSpinner from "@/components/LoadingSpinner";
import AnalysisResults from "@/components/AnalysisResults";

export default function HomePage() {
  const [step, setStep] = useState<AppStep>("upload");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<CVUploadResponse | null>(null);
  const [analysisResult, setAnalysisResult] =
    useState<CVAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Handle file selection ──
  const handleFileSelected = async (file: File) => {
    setError(null);
    setIsUploading(true);

    try {
      // Step 1: Upload
      const uploadResp = await uploadCV(file);
      setUploadInfo(uploadResp);

      // Step 2: Analyse
      setStep("analyzing");
      setIsUploading(false);

      const result = await analyzeCV(uploadResp.file_id);
      setAnalysisResult(result);
      setStep("results");
    } catch (err: any) {
      setError(err.message ?? "Something went wrong. Please try again.");
      setStep("upload");
      setIsUploading(false);
    }
  };

  // ── Reset to upload screen ──
  const handleReset = () => {
    setStep("upload");
    setUploadInfo(null);
    setAnalysisResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 px-6 py-10">
        {/* ── Error banner ── */}
        {error && (
          <div className="mx-auto mb-6 max-w-2xl rounded-lg bg-red-50 border border-red-200 p-4">
            <div className="flex items-center gap-2">
              <svg
                className="h-5 w-5 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
              <p className="text-sm font-medium text-red-800">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-xs text-red-600 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ── Step: Upload ── */}
        {step === "upload" && (
          <div>
            <div className="mx-auto max-w-2xl text-center mb-10">
              <h2 className="text-3xl font-bold text-gray-900">
                Analyse Your CV
              </h2>
              <p className="mt-3 text-gray-500">
                Upload your resume and receive AI-powered feedback with
                actionable recommendations, job matching, and a quality score.
              </p>
            </div>
            <FileUpload
              onFileSelected={handleFileSelected}
              isUploading={isUploading}
            />
          </div>
        )}

        {/* ── Step: Analyzing ── */}
        {step === "analyzing" && <LoadingSpinner />}

        {/* ── Step: Results ── */}
        {step === "results" && analysisResult && (
          <AnalysisResults result={analysisResult} onReset={handleReset} />
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-400">
        CV Analysis v2.0 &mdash; Built with Next.js, FastAPI, LangChain &amp;
        Claude Sonnet
      </footer>
    </div>
  );
}
