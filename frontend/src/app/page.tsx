'use client';

import React, { useState, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import Head from 'next/head';
import ReportDisplay from '../components/ReportDisplay'; 


interface ApiErrorDetail { detail: string; }

// Define structure matching backend's structured raw report
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

interface ApiResponse {
  structured_report: StructuredReportData;
  agent_analysis: string;
  slack_notification_status: string;
  request_id?: string;
}

const Home: React.FC = () => {
  // State variables - adjusted for structured report
  const [structuredReport, setStructuredReport] = useState<StructuredReportData | null>(null); // Store structured data
  const [agentAnalysis, setAgentAnalysis] = useState<string>('');
  const [slackStatus, setSlackStatus] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);

  // fetchReport function
  const fetchReport = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setRequestId(null);
    setStructuredReport(null);
    setAgentAnalysis('');
    setSlackStatus('');
    console.log("Frontend: Triggering report generation...");

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const reportEndpoint = `${backendUrl}/api/v1/report`;

    try {
      
      const response = await axios.get<{
          raw_report: string;
          agent_analysis: string;
          slack_notification_status: string;
          request_id?: string;
      }>(reportEndpoint);

      console.log("Frontend: Backend response received:", response.data);

      if (response.data) {
          // *** PARSE THE RAW REPORT STRING INTO STRUCTURED DATA ***
         
          const parsedStructure: StructuredReportData = {
            trello: { lines: [] },
            email: { lines: [], count: 0 },
            slack: { lines: [], count: 0 }
        };

        // Normalize line endings and split into sections
        const normalizedReport = response.data.raw_report
            .replace(/\r\n/g, '\n')  // Normalize Windows line endings
            .replace(/\n{3,}/g, '\n\n');  // Normalize multiple newlines to double newlines

        // Split into sections using a more robust pattern
        const sections = normalizedReport.split(/\n(?=\*\*)/);
        
        sections.forEach(section => {
            const lines = section.trim().split('\n');
            if (lines.length === 0) return;

            const sectionTitle = lines[0].trim();
            
            if (sectionTitle.includes("Trello")) {
                parsedStructure.trello.lines = lines;
            } else if (sectionTitle.includes("Email Updates")) {
                
                parsedStructure.email.lines = lines;
                
                const count = lines.filter(l => l.trim().startsWith("- **From:**")).length;
                parsedStructure.email.count = count;
                console.log("Email section found:", lines);
                console.log("Email count:", count);
            } else if (sectionTitle.includes("Slack Messages")) {
                parsedStructure.slack.lines = lines;
                parsedStructure.slack.count = lines.filter(l => l.trim().startsWith("- **")).length;
            }
        });
          setStructuredReport(parsedStructure);
          // *** END PARSING ***

          setAgentAnalysis(response.data.agent_analysis || 'Analysis data missing.');
          setSlackStatus(response.data.slack_notification_status || 'Slack status unknown.');
          setRequestId(response.data.request_id || null);
      } else {
        setError('Received unexpected data format from backend.');
      }

    } catch (err) {
        console.error("Frontend: Error fetching report:", err);
        let errorMessage = '...'; 
        if (axios.isAxiosError(err)) {
             const axiosError = err as AxiosError<ApiErrorDetail>;
             errorMessage = `Error ${axiosError.response?.status}: ${axiosError.response?.data?.detail || axiosError.message}`;
        } else if (err instanceof Error) { errorMessage = `Error: ${err.message}`; }
        setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <>
      <Head>
        <title>Project Status Reporter</title>
        <meta name="description" content="Automated Project Status Reporting with AI Analysis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8 md:py-12 max-w-4xl">
        <h1 className="text-3xl md:text-4xl font-bold text-center mb-8 text-gray-800">
          Project Status Reporter
        </h1>

        <div className="text-center mb-8">
          <button
            onClick={fetchReport}
            disabled={isLoading}
            className={`px-6 py-3 rounded-md font-semibold text-white transition-colors duration-200 ease-in-out ${
              isLoading
                ? 'bg-indigo-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2'
            }`}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating Report...
              </>
            ) : (
              'Generate Status Report'
            )}
          </button>
        </div>

        {/* Status and Error Display */}
        <div className="text-center mb-6 min-h-[2rem]"> {/* Prevents layout shift */}
          {isLoading && <p className="text-gray-600 animate-pulse">Fetching latest status...</p>}
          {error && <p className="text-red-600 font-semibold bg-red-100 p-3 rounded-md">Error: {error}</p>}
          {!isLoading && !error && slackStatus && (
            <p className={`font-semibold p-3 rounded-md ${slackStatus.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
              Slack Notification: {slackStatus}
            </p>
          )}
          {!isLoading && !error && requestId && (
            <p className="text-xs text-gray-400 mt-1">Request ID: {requestId}</p>
          )}
        </div>

         {/* Display Reports - Pass structured data */}
         {!isLoading && !error && (structuredReport || agentAnalysis) && (
           <ReportDisplay
             structuredReportData={structuredReport} // Pass the parsed structured data
             agentAnalysis={agentAnalysis}
           />
         )}
      </main>
    </>
  );
};

export default Home;