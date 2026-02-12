/**
 * LoadingSpinner — displayed during the analysis pipeline.
 *
 * Shows animated progress stages to keep the user informed.
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

"use client";

const stages = [
  { label: "Loading document...", icon: "📄" },
  { label: "Chunking text...", icon: "✂️" },
  { label: "Extracting information...", icon: "🔍" },
  { label: "Matching job roles...", icon: "🎯" },
  { label: "Generating recommendations...", icon: "💡" },
];

export default function LoadingSpinner() {
  return (
    <div className="mx-auto max-w-md py-16 text-center">
      {/* Spinner */}
      <div className="mx-auto mb-8 h-16 w-16 animate-spin rounded-full border-4 border-gray-200 border-t-primary-600" />

      <h2 className="text-xl font-bold text-gray-900">
        Analyzing your CV...
      </h2>
      <p className="mt-2 text-sm text-gray-500">
        Our AI is running the full pipeline. This may take 30–60 seconds.
      </p>

      {/* Pipeline stages */}
      <div className="mt-8 space-y-3 text-left">
        {stages.map((stage, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-lg bg-white p-3 shadow-sm border border-gray-100 animate-pulse"
            style={{ animationDelay: `${i * 0.3}s` }}
          >
            <span className="text-lg">{stage.icon}</span>
            <span className="text-sm text-gray-600">{stage.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
