import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, gql } from '@apollo/client';
import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { ArrowUturnLeftIcon, UserPlusIcon, ArrowDownOnSquareIcon } from '@heroicons/react/24/outline';

const GET_SPREADSHEET_DATA = gql`
  query SpreadsheetById($id: UUID!) {
    spreadsheetById(id: $id) {
      id
      name
      workspace {
        id
        name
      }
      cells {
        id
        row
        column
        content
        evaluatedContent
      }
    }
  }
`;

const UPDATE_CELL = gql`
    mutation UpdateCell($spreadsheetId: UUID!, $row: Int!, $column: Int!, $content: String!) {
        updateCell(spreadsheetId: $spreadsheetId, row: $row, column: $column, content: $content) {
            cell {
                id
                content
                evaluatedContent
            }
        }
    }
`;


const ROWS = 40;
const COLS = 12;
const SSRF_KEYWORDS = ['=IMPORT_CSV(', '=FETCH_URL(', '=GET_DATA('];

export default function Spreadsheet() {
    const { id } = useParams();
    const [cells, setCells] = useState({});
    const [activeCell, setActiveCell] = useState(null);
    const [inputValue, setInputValue] = useState('');

    const { loading, error, data, refetch } = useQuery(GET_SPREADSHEET_DATA, {
        variables: { id },
        notifyOnNetworkStatusChange: true,
    });

    const [updateCell] = useMutation(UPDATE_CELL, {
        onError: (err) => toast.error(err.message),
    });

    // This useEffect hook is the key to the automatic refresh.
    // It runs whenever the `data` from the useQuery hook changes (e.g., after a refetch),
    // and updates the local `cells` state, which causes the UI to re-render.
    useEffect(() => {
        if (data?.spreadsheetById?.cells) {
            const newCells = {};
            data.spreadsheetById.cells.forEach(cell => {
                newCells[`${cell.row}-${cell.column}`] = { content: cell.content, evaluated: cell.evaluatedContent };
            });
            setCells(newCells);
        }
    }, [data]);

    useEffect(() => {
        if (activeCell) {
            setInputValue(cells[activeCell]?.content || '');
        }
    }, [activeCell, cells]);

    const handleCellBlur = () => {
        if (!activeCell || (cells[activeCell]?.content || '') === inputValue) return;
        
        const [row, col] = activeCell.split('-').map(Number);
        const isSsrFormula = SSRF_KEYWORDS.some(keyword => inputValue.toUpperCase().startsWith(keyword));

        updateCell({ variables: { spreadsheetId: id, row, column: col, content: inputValue }})
        .then(() => {
            const newCells = { ...cells };
            newCells[activeCell] = { ...newCells[activeCell], content: inputValue };
            setCells(newCells);
            toast.success('Cell updated!');

            if (isSsrFormula) {
                let toastId = toast.loading('Executing remote formula...');
                let pollCount = 0;
                const maxPolls = 5;

                const pollInterval = setInterval(async () => {
                    pollCount++;
                    const { data: newData } = await refetch();
                    const updatedCellData = newData?.spreadsheetById?.cells.find(c => c.row === row && c.column === col);
                    
                    if (updatedCellData && updatedCellData.evaluatedContent && updatedCellData.evaluatedContent !== updatedCellData.content) {
                        toast.success('Data loaded!', { id: toastId });
                        clearInterval(pollInterval);
                    } else if (pollCount >= maxPolls) {
                        toast.error('Request timed out.', { id: toastId });
                        clearInterval(pollInterval);
                    }
                }, 2000);
            } else {
                refetch();
            }
        });
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            e.target.blur();
        }
    }

    const handleExport = async () => {
        const token = localStorage.getItem('authToken');
        if (!token) { toast.error("You are not logged in."); return; }
        toast.loading('Preparing download...');
        const exportUrl = `/export/${data.spreadsheetById.workspace.id}`;
        try {
            const response = await fetch(exportUrl, {
                headers: { 'Authorization': `JWT ${token}` }
            });
            toast.dismiss();
            if (!response.ok) throw new Error('Export failed. Please try again.');
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `export_${data.spreadsheetById.workspace.name}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
            toast.success('Download started!');
        } catch (err) {
            toast.dismiss();
            toast.error(err.message);
        }
    };

    if (loading && !Object.keys(cells).length) return <div className="flex justify-center items-center h-screen"><p>Loading Spreadsheet...</p></div>;
    if (error) return <p>Error loading spreadsheet: {error.message}</p>;
    if (!data || !data.spreadsheetById) return <div className="flex justify-center items-center h-screen"><p>Spreadsheet not found.</p></div>;

    const { name, workspace } = data.spreadsheetById;
    const getColumnName = (index) => String.fromCharCode(65 + index);

    return (
        <div className="flex flex-col h-screen bg-slate-100">
            <header className="bg-white p-3 shadow-md z-10">
                <div className="flex items-center justify-between">
                    <div>
                        <Link to="/" className="flex items-center text-sm text-blue-600 hover:underline mb-1">
                            <ArrowUturnLeftIcon className="h-4 w-4 mr-1"/>
                            Back to Dashboard
                        </Link>
                        <h1 className="text-xl font-bold text-slate-800">{name}</h1>
                        <p className="text-xs text-slate-500">in workspace "{workspace.name}"</p>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button className="flex items-center bg-white border border-slate-300 text-slate-700 px-3 py-2 rounded-lg text-sm font-medium hover:bg-slate-50">
                            <UserPlusIcon className="h-5 w-5 mr-2"/> Invite
                        </button>
                        <button onClick={handleExport} className="flex items-center bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
                           <ArrowDownOnSquareIcon className="h-5 w-5 mr-2"/> Export Data
                        </button>
                    </div>
                </div>
                <div className="mt-3">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onBlur={handleCellBlur}
                        onKeyDown={handleKeyDown}
                        placeholder={activeCell ? `Editing ${getColumnName(parseInt(activeCell.split('-')[1]))}${parseInt(activeCell.split('-')[0]) + 1}` : 'Select a cell to edit'}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={!activeCell}
                    />
                </div>
            </header>
            <main className="flex-grow overflow-auto p-4">
                <table className="table-fixed border-collapse border border-slate-300 w-full">
                    <thead>
                        <tr>
                            <th className="w-12 bg-slate-200 border border-slate-300"></th>
                            {[...Array(COLS)].map((_, i) => (
                                <th key={i} className="w-32 bg-slate-200 border border-slate-300 font-semibold">{getColumnName(i)}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {[...Array(ROWS)].map((_, r) => (
                            <tr key={r}>
                                <td className="text-center bg-slate-200 border border-slate-300 font-semibold">{r + 1}</td>
                                {[...Array(COLS)].map((_, c) => {
                                    const cellKey = `${r}-${c}`;
                                    const isActive = activeCell === cellKey;
                                    const cellData = cells[cellKey];
                                    return (
                                        <td
                                            key={c}
                                            className={`border border-slate-300 p-0 ${isActive ? 'ring-2 ring-blue-500 ring-inset' : ''}`}
                                            onClick={() => setActiveCell(cellKey)}
                                        >
                                            <div className="w-full h-full px-2 py-1 outline-none truncate">
                                                {cellData?.evaluated || cellData?.content || ''}
                                            </div>
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </main>
        </div>
    );
}


