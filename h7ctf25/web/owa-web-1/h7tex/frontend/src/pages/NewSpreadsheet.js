// frontend/src/pages/NewSpreadsheet.js

import { useState } from 'react';
import { useMutation, gql } from '@apollo/client';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowUturnLeftIcon } from '@heroicons/react/24/outline';

const CREATE_SPREADSHEET = gql`
    mutation CreateSpreadsheet($workspaceId: UUID!, $name: String!) {
        createSpreadsheet(workspaceId: $workspaceId, name: $name) {
            spreadsheet {
                id
                name
            }
        }
    }
`;

export default function NewSpreadsheet() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [name, setName] = useState('');
    const workspaceId = searchParams.get('ws');

    const [createSpreadsheet, { loading }] = useMutation(CREATE_SPREADSHEET, {
        onCompleted: (data) => {
            toast.success('Spreadsheet created!');
            // Redirect to the new spreadsheet page
            navigate(`/spreadsheet/${data.createSpreadsheet.spreadsheet.id}`);
        },
        onError: (err) => toast.error(err.message),
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        if (name.trim() && workspaceId) {
            createSpreadsheet({ variables: { name: name.trim(), workspaceId } });
        } else {
            toast.error('Workspace ID is missing or name is empty.');
        }
    };

    return (
        <div className="min-h-screen bg-slate-100 flex justify-center items-center">
            <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-lg">
                 <a href="/" className="flex items-center text-sm text-blue-600 hover:underline mb-4">
                    <ArrowUturnLeftIcon className="h-4 w-4 mr-1"/>
                    Back to Dashboard
                </a>
                <h2 className="text-2xl font-bold text-center text-slate-700 mb-6">Create New Spreadsheet</h2>
                <form onSubmit={handleSubmit}>
                    <input
                        type="text"
                        placeholder="Spreadsheet Name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full mt-6 bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
                    >
                        {loading ? 'Creating...' : 'Create Spreadsheet'}
                    </button>
                </form>
            </div>
        </div>
    );
}
