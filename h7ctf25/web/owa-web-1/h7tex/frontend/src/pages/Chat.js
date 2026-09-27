import { useQuery, gql } from '@apollo/client';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { ArrowUturnLeftIcon, UserCircleIcon } from '@heroicons/react/24/solid';

// --- THE FIX IS HERE ---
// The query has been updated from "chats" to "userChats" to match the backend schema.
const GET_CHATS = gql`
  query GetUserChats {
    userChats {
      id
      participants {
        id
        username
      }
      messages {
        id
        sender {
          id
          username
        }
        content
        timestamp
      }
    }
  }
`;
// --- END FIX ---

export default function Chat() {
    const { user } = useAuth();
    const { loading, error, data } = useQuery(GET_CHATS);

    if (loading) return <div className="flex justify-center items-center h-screen"><p>Loading Chats...</p></div>;
    if (error) return <p>Error loading chats: {error.message}</p>;

    // Also updated here to access the correct data property
    const chat = data.userChats[0]; 

    if (!chat) {
        return (
             <div className="flex flex-col items-center justify-center h-screen bg-slate-100">
                <h2 className="text-xl font-semibold mb-4">No messages yet.</h2>
                 <Link to="/" className="flex items-center text-sm text-blue-600 hover:underline">
                    <ArrowUturnLeftIcon className="h-4 w-4 mr-1"/>
                    Back to Dashboard
                </Link>
            </div>
        )
    }

    const getOtherParticipant = (participants) => {
        return participants.find(p => p.id !== user.id);
    }

    return (
        <div className="flex flex-col h-screen bg-slate-100">
            <header className="bg-white p-4 shadow-md z-10 flex items-center justify-between">
                <div className="flex items-center">
                    <UserCircleIcon className="h-8 w-8 text-slate-500 mr-3" />
                    <div>
                        <h1 className="text-lg font-bold text-slate-800">
                            Chat with {getOtherParticipant(chat.participants)?.username || 'Support'}
                        </h1>
                        <p className="text-xs text-green-500 font-semibold">Online</p>
                    </div>
                </div>
                <Link to="/" className="flex items-center text-sm text-blue-600 hover:underline">
                    <ArrowUturnLeftIcon className="h-4 w-4 mr-1"/>
                    Back to Dashboard
                </Link>
            </header>
            <main className="flex-grow overflow-auto p-4 space-y-4">
                {chat.messages.map(message => {
                    const isSender = message.sender.id === user.id;
                    return (
                        <div key={message.id} className={`flex items-end gap-2 ${isSender ? 'justify-end' : 'justify-start'}`}>
                             {!isSender && <UserCircleIcon className="h-8 w-8 text-slate-400" />}
                             <div className={`max-w-lg px-4 py-3 rounded-2xl ${isSender ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white text-slate-700 rounded-bl-none shadow-sm'}`}>
                                <p className="text-sm">{message.content}</p>
                             </div>
                        </div>
                    );
                })}
            </main>
        </div>
    );
}


