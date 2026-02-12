/**
 * AnalysisResults — displays the full CV analysis output.
 *
 * Sections:
 *   1. Score & Summary
 *   2. Skills
 *   3. Experience
 *   4. Education
 *   5. Job Matches
 *   6. Recommendations
 *   7. Agent Q&A
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

"use client";

import { useState } from "react";
import type {
  CVAnalysisResult,
  AgentQueryResponse,
} from "@/types";
import { queryAgent } from "@/lib/api";

interface Props {
  result: CVAnalysisResult;
  onReset: () => void;
}

// ---------------------------------------------------------------------------
// Helper: priority badge
// ---------------------------------------------------------------------------
function PriorityBadge({ priority }: { priority: string }) {
  const cls =
    priority === "high"
      ? "badge-high"
      : priority === "medium"
        ? "badge-medium"
        : "badge-low";
  return <span className={cls}>{priority}</span>;
}

// ---------------------------------------------------------------------------
// Helper: score ring
// ---------------------------------------------------------------------------
function ScoreRing({ score }: { score: number }) {
  const color =
    score >= 75
      ? "text-green-500"
      : score >= 50
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="flex flex-col items-center">
      <div
        className={`flex h-28 w-28 items-center justify-center rounded-full border-4 ${
          score >= 75
            ? "border-green-200"
            : score >= 50
              ? "border-yellow-200"
              : "border-red-200"
        }`}
      >
        <span className={`text-3xl font-bold ${color}`}>
          {Math.round(score)}
        </span>
      </div>
      <span className="mt-2 text-sm font-medium text-gray-500">
        Quality Score
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skill level bar
// ---------------------------------------------------------------------------
function SkillBar({ level }: { level: string }) {
  const widths: Record<string, string> = {
    beginner: "w-1/4",
    intermediate: "w-2/4",
    advanced: "w-3/4",
    expert: "w-full",
  };
  const colors: Record<string, string> = {
    beginner: "bg-blue-300",
    intermediate: "bg-blue-400",
    advanced: "bg-blue-500",
    expert: "bg-blue-600",
  };

  return (
    <div className="h-2 w-24 rounded-full bg-gray-200">
      <div
        className={`h-full rounded-full ${widths[level] ?? "w-2/4"} ${colors[level] ?? "bg-blue-400"}`}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function AnalysisResults({ result, onReset }: Props) {
  const [question, setQuestion] = useState("");
  const [agentAnswer, setAgentAnswer] = useState<AgentQueryResponse | null>(
    null
  );
  const [askingAgent, setAskingAgent] = useState(false);

  const handleAskAgent = async () => {
    if (!question.trim()) return;
    setAskingAgent(true);
    try {
      const resp = await queryAgent({
        file_id: result.file_id,
        question: question.trim(),
      });
      setAgentAnswer(resp);
    } catch (err: any) {
      setAgentAnswer({
        answer: `Error: ${err.message}`,
        sources: [],
        tool_calls: [],
      });
    } finally {
      setAskingAgent(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* ── Top bar ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {result.candidate_name}
          </h2>
          {result.email && (
            <p className="text-sm text-gray-500">{result.email}</p>
          )}
        </div>
        <button onClick={onReset} className="btn-secondary">
          Analyse Another CV
        </button>
      </div>

      {/* ── Score + Summary ── */}
      <div className="card flex flex-col md:flex-row gap-8 items-center">
        <ScoreRing score={result.overall_score} />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Professional Summary
          </h3>
          <p className="text-sm leading-relaxed text-gray-600">
            {result.summary || "No summary extracted."}
          </p>
        </div>
      </div>

      {/* ── Skills ── */}
      {result.skills.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Skills ({result.skills.length})
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {result.skills.map((skill, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 p-3"
              >
                <div>
                  <span className="text-sm font-medium text-gray-800">
                    {skill.name}
                  </span>
                  {skill.years && (
                    <span className="ml-2 text-xs text-gray-400">
                      {skill.years}y
                    </span>
                  )}
                </div>
                <SkillBar level={skill.level} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Experience ── */}
      {result.experience.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Work Experience
          </h3>
          <div className="space-y-4">
            {result.experience.map((exp, i) => (
              <div key={i} className="border-l-2 border-primary-300 pl-4">
                <div className="flex items-baseline justify-between">
                  <h4 className="font-medium text-gray-900">{exp.title}</h4>
                  <span className="text-xs text-gray-400">
                    {exp.duration}
                  </span>
                </div>
                <p className="text-sm text-gray-500">
                  {exp.company}{" "}
                  <span className="text-xs text-gray-400">
                    ({exp.domain})
                  </span>
                </p>
                {exp.highlights.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {exp.highlights.map((h, j) => (
                      <li
                        key={j}
                        className="text-xs text-gray-600 before:mr-1 before:content-['•']"
                      >
                        {h}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Education ── */}
      {result.education.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Education
          </h3>
          <div className="space-y-3">
            {result.education.map((edu, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {edu.degree}
                  </p>
                  <p className="text-xs text-gray-500">{edu.institution}</p>
                </div>
                <span className="text-xs text-gray-400">{edu.year}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Job Matches ── */}
      {result.job_matches.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Job Matches
          </h3>
          <div className="space-y-3">
            {result.job_matches.map((match, i) => (
              <div
                key={i}
                className="flex items-center gap-4 rounded-lg border border-gray-100 bg-gray-50 p-4"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
                  {Math.round(match.similarity_score * 100)}%
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{match.role}</p>
                  <p className="text-xs text-gray-500 line-clamp-1">
                    {match.reason}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recommendations ── */}
      {result.recommendations.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Improvement Recommendations
          </h3>
          <div className="space-y-3">
            {result.recommendations.map((rec, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-100 bg-gray-50 p-4"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    {rec.category}
                  </span>
                  <PriorityBadge priority={rec.priority} />
                </div>
                <p className="text-sm text-gray-700">{rec.suggestion}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Agent Q&A ── */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Ask AI About This CV
        </h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAskAgent()}
            placeholder="e.g. Does this CV mention cloud certifications?"
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm
                       focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            disabled={askingAgent}
          />
          <button
            onClick={handleAskAgent}
            disabled={askingAgent || !question.trim()}
            className="btn-primary"
          >
            {askingAgent ? "Thinking..." : "Ask"}
          </button>
        </div>

        {agentAnswer && (
          <div className="mt-4 rounded-lg bg-gray-50 p-4 border border-gray-100">
            <p className="text-sm whitespace-pre-wrap text-gray-700">
              {agentAnswer.answer}
            </p>
            {agentAnswer.tool_calls.length > 0 && (
              <p className="mt-2 text-xs text-gray-400">
                Tools used: {agentAnswer.tool_calls.join(", ")}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
