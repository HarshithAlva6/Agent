'use client'; 

import React, { useState, useEffect, FormEvent } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

interface Claim {
  id: number;
  customer_id: string;
  description: string;
  status: string;
  submission_date: string;
}

export default function Home() {
  const [customerId, setCustomerId] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    fetchClaims();
  }, []); 

  const fetchClaims = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/claims/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setClaims(data);
    } catch (e) {
      console.error("Failed to fetch claims:", e);
      setError("Failed to load claims. Please check the backend server.");
    } finally {
      setLoading(false);
    }
  };

  // Function to handle new claim submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault(); 
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/claims/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ customer_id: customerId, description: description }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || response.statusText}`);
      }

      const newClaim = await response.json();
      setClaims((prevClaims) => [newClaim, ...prevClaims]); 
      setCustomerId(''); 
      setDescription('');
      setMessage('Claim submitted successfully!');
    } catch (e: any) {
      console.error("Failed to submit claim:", e);
      setMessage(`Error submitting claim: ${e.message}`);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };


  // NEW FUNCTION: Handles triggering the AI Validation endpoint
  const triggerValidation = async (claimId: number) => {
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/claims/${claimId}/validate`, {
        method: 'PUT', 
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || response.statusText}`);
      }

      const validatedClaim: Claim = await response.json();
      setClaims((prevClaims) =>
        prevClaims.map((claim) => (claim.id === claimId ? validatedClaim : claim))
      );
      setMessage(`Claim ${claimId} validated by AI! New status: "${validatedClaim.status}"`);
    } catch (e: any) {
      console.error("Failed to validate claim:", e);
      setMessage(`Error validating claim ${claimId}: ${e.message}`);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };


  // Function to update a claim's status (e.g., for manual progression)
  const triggerValidationManual = async (claimId: number, newStatus: string) => {
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/claims/${claimId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || response.statusText}`);
      }

      const updatedClaim = await response.json();
      setClaims((prevClaims) =>
        prevClaims.map((claim) => (claim.id === claimId ? updatedClaim : claim))
      );
      setMessage(`Claim ${claimId} status updated to "${newStatus}"!`);
    } catch (e: any) {
      console.error("Failed to update claim status manually:", e);
      setMessage(`Error updating claim ${claimId} status: ${e.message}`);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 lg:p-8 font-sans">
      <div className="max-w-6xl mx-auto bg-white shadow-xl rounded-xl p-6 sm:p-8 lg:p-10">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 text-center mb-8">
          WayTOO Claims Management Dashboard
        </h1>

        {/* Claim Submission Form */}
        <section className="mb-10 p-6 bg-blue-50 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold text-blue-800 mb-6 text-center">Submit New Claim</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="customerId" className="block text-sm font-medium text-gray-700 mb-1">
                Customer ID:
              </label>
              <input
                type="text"
                id="customerId"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                placeholder="e.g., WAYTOO-CUST-001"
              />
            </div>
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description:
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 resize-y"
                placeholder="e.g., Missing 5mm screw from aircraft wing assembly, order #A1B2C3."
              ></textarea>
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-150 ease-in-out font-semibold text-lg"
              disabled={loading}
            >
              {loading ? 'Submitting...' : 'Submit Claim'}
            </button>
          </form>
          {message && (
            <p className={`mt-4 text-center font-medium ${error ? 'text-red-600' : 'text-green-600'}`}>
              {message}
            </p>
          )}
        </section>

        {/* Claims List */}
        <section className="p-6 bg-gray-50 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">All Claims</h2>
          {loading && !claims.length && <p className="text-center text-gray-600">Loading claims...</p>}
          {error && <p className="text-center text-red-600 font-medium">{error}</p>}

          {!loading && claims.length === 0 && !error && (
            <p className="text-center text-gray-600">No claims found. Submit one above!</p>
          )}

          {claims.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submission Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {claims.map((claim) => (
                    <tr key={claim.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{claim.id}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{claim.customer_id}</td>
                      <td className="px-4 py-3 text-sm text-gray-700 max-w-xs overflow-hidden text-ellipsis">{claim.description}</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                          ${claim.status === 'submitted' ? 'bg-yellow-100 text-yellow-800' : ''}
                          ${claim.status === 'validated' ? 'bg-green-100 text-green-800' : ''}
                          ${claim.status === 'root_cause_identified' ? 'bg-blue-100 text-blue-800' : ''}
                          ${claim.status === 'resolved' ? 'bg-purple-100 text-purple-800' : ''}
                          ${claim.status === 'escalated_to_ops' ? 'bg-red-100 text-red-800' : ''}
                        `}>
                          {claim.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                        {new Date(claim.submission_date).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex space-x-2">
                          {claim.status === 'submitted' && (
                            <button
                              onClick={() => triggerValidation(claim.id)}
                              className="text-indigo-600 hover:text-indigo-900 px-3 py-1 border border-indigo-300 rounded-md text-xs font-semibold"
                              disabled={loading}
                            >
                              Validate (AI)
                            </button>
                          )}
                          {/* Manual progression buttons (adjust as per your workflow) */}
                          {(claim.status === 'validated' || claim.status === 'pending_manual_review') && (
                            <button
                              onClick={() => triggerValidationManual(claim.id, 'root_cause_identified')}
                              className="text-blue-600 hover:text-blue-900 px-3 py-1 border border-blue-300 rounded-md text-xs font-semibold"
                              disabled={loading}
                            >
                              Analyze (Manual)
                            </button>
                          )}
                          {claim.status === 'root_cause_identified' && (
                            <button
                              onClick={() => triggerValidationManual(claim.id, 'resolved')}
                              className="text-purple-600 hover:text-purple-900 px-3 py-1 border border-purple-300 rounded-md text-xs font-semibold"
                              disabled={loading}
                            >
                              Resolve (Manual)
                            </button>
                          )}
                          {/* Example: Re-open a resolved claim */}
                          {claim.status === 'resolved' && (
                            <button
                              onClick={() => triggerValidationManual(claim.id, 'pending_manual_review')}
                              className="text-gray-600 hover:text-gray-900 px-3 py-1 border border-gray-300 rounded-md text-xs font-semibold"
                              disabled={loading}
                            >
                              Re-open
                            </button>
                          )}
                          {/* Add more status progression buttons as needed */}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
