/**
 * Header component — top navigation bar.
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

"use client";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo & title */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-lg">
            CV
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">
              CV Analysis
            </h1>
            <p className="text-xs text-gray-500">
              AI-Powered Resume Reviewer
            </p>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-400">
            Powered by Claude Sonnet &amp; LangChain
          </span>
        </div>
      </div>
    </header>
  );
}
