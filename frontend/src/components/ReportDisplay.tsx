// components/ReportDisplay.tsx
"use client"
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { FaTrello } from 'react-icons/fa';
import { MdEmail } from 'react-icons/md';
import { FaSlack } from 'react-icons/fa';
import { IoIosArrowDown, IoIosArrowUp } from 'react-icons/io';

// --- Helper: Content Display Component ---
const ContentDisplay: React.FC<{ lines: string[] }> = ({ lines }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const maxLines = 5;

  if (lines.length <= maxLines) {
    return <ReactMarkdown>{lines.join('\n')}</ReactMarkdown>;
  }

  const displayLines = isExpanded ? lines : lines.slice(0, maxLines);
  const hasMore = lines.length > maxLines;

  return (
    <div>
      <div className={`${!isExpanded ? 'max-h-[200px] overflow-y-auto' : ''}`}>
        <ReactMarkdown>{displayLines.join('\n')}</ReactMarkdown>
      </div>
      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          {isExpanded ? (
            <>
              Show less <IoIosArrowUp className="ml-1" />
            </>
          ) : (
            <>
              Show more <IoIosArrowDown className="ml-1" />
            </>
          )}
        </button>
      )}
    </div>
  );
};

// --- Helper: Email Content Display Component ---
const EmailContentDisplay: React.FC<{ lines: string[] }> = ({ lines }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const maxLines = 3; // Show only 3 lines initially for emails

  
  const emailEntries = lines.reduce((acc: string[][], line: string) => {
    if (line.trim().startsWith('- **From:**')) {
      acc.push([line]);
    } else if (acc.length > 0 && line.trim().startsWith('**Subject:**')) {
      acc[acc.length - 1].push(line);
    }
    return acc;
  }, []);

  if (emailEntries.length <= maxLines) {
    return (
      <div>
        {emailEntries.map((entry, index) => (
          <div key={index} className="mb-4 last:mb-0">
            <ReactMarkdown>{entry.join('\n')}</ReactMarkdown>
          </div>
        ))}
      </div>
    );
  }

  const displayEntries = isExpanded ? emailEntries : emailEntries.slice(0, maxLines);
  const hasMore = emailEntries.length > maxLines;

  return (
    <div>
      <div className={`${!isExpanded ? 'max-h-[150px] overflow-y-auto' : ''}`}>
        {displayEntries.map((entry, index) => (
          <div key={index} className="mb-4 last:mb-0">
            <ReactMarkdown>{entry.join('\n')}</ReactMarkdown>
          </div>
        ))}
      </div>
      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          {isExpanded ? (
            <>
              Show less <IoIosArrowUp className="ml-1" />
            </>
          ) : (
            <>
              Show {emailEntries.length - maxLines} more emails <IoIosArrowDown className="ml-1" />
            </>
          )}
        </button>
      )}
    </div>
  );
};

interface ReportSection {
  lines: string[];
  count?: number;
  overdue_count?: number;
}

interface StructuredReportData {
  trello: ReportSection;
  email: ReportSection;
  slack: ReportSection;
}

interface ReportDisplayProps {
  structuredReportData: StructuredReportData | null;
  agentAnalysis: string;
}

// Helper to render section lines as markdown
const renderLines = (lines: string[]) => {
   
    return <ReactMarkdown>{lines.join('\n')}</ReactMarkdown>;
};

const ReportDisplay: React.FC<ReportDisplayProps> = ({ structuredReportData, agentAnalysis }) => {
  if (!structuredReportData) return null;

  const { trello, email, slack } = structuredReportData;

  return (
    <div className="mt-6 space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">Project Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        {/* Trello Card */}
        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-700 mb-3 flex items-center">
            <FaTrello className="w-5 h-5 mr-2 text-blue-600" /> Trello Tasks
          </h3>
          <div className="prose prose-sm max-w-none text-gray-600">
            <ContentDisplay lines={trello.lines} />
          </div>
        </div>

        {/* Email Card */}
        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-700 mb-3 flex items-center">
            <MdEmail className="w-5 h-5 mr-2 text-red-600" /> Email Updates ({email.count ?? 0})
          </h3>
          <div className="prose prose-sm max-w-none text-gray-600">
            <EmailContentDisplay lines={email.lines.slice(1)} />
          </div>
          {email.count === 0 && <p className="text-sm text-gray-500 italic">No new emails</p>}
        </div>

        {/* Slack Card */}
        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-700 mb-3 flex items-center">
            <FaSlack className="w-5 h-5 mr-2 text-green-600" /> Slack Messages ({slack.count ?? 0})
          </h3>
          <div className="prose prose-sm max-w-none text-gray-600">
            <ContentDisplay lines={slack.lines.slice(1)} />
          </div>
          {slack.count === 0 && <p className="text-sm text-gray-500 italic">No new messages</p>}
        </div>
      </div>

      {/* Agent Analysis Section */}
      <div className="mt-8 p-4 md:p-6 bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 border border-indigo-100 rounded-lg shadow-md">
        <h2 className="text-xl md:text-2xl font-semibold text-indigo-800 mb-3 border-b border-indigo-200 pb-2">
          📊 Project Analysis
        </h2>
        <div className="prose prose-sm sm:prose-base max-w-none text-gray-800">
          <ReactMarkdown>{agentAnalysis}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default ReportDisplay;