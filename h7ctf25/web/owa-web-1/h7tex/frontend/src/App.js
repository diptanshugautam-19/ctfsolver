import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AuthPage from './pages/Auth';
import Dashboard from './pages/Dashboard';
import Spreadsheet from './pages/Spreadsheet';
import NewSpreadsheet from './pages/NewSpreadsheet';
import Chat from './pages/Chat'; // <-- Import the new Chat page
import { Toaster } from 'react-hot-toast';

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        Loading...
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={!user ? <AuthPage /> : <Navigate to="/" />} />
      <Route path="/auth" element={!user ? <AuthPage /> : <Navigate to="/" />} />
      <Route path="/spreadsheet/new" element={user ? <NewSpreadsheet /> : <Navigate to="/auth" />} />
      <Route path="/spreadsheet/:id" element={user ? <Spreadsheet /> : <Navigate to="/auth" />} />
      <Route path="/chat" element={user ? <Chat /> : <Navigate to="/auth" />} /> {/* <-- Add the Chat route */}
      <Route path="/" element={user ? <Dashboard /> : <Navigate to="/auth" />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <div>
          <Toaster position="top-center" reverseOrder={false} />
          <AppContent />
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;


