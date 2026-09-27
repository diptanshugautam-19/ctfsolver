import { useState } from 'react';
import { useMutation, gql } from '@apollo/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import { ShieldCheckIcon } from '@heroicons/react/24/outline';

const LOGIN_MUTATION = gql`
  mutation TokenAuth($username: String!, $password: String!) {
    tokenAuth(username: $username, password: $password) {
      token
    }
  }
`;

export default function Auth() {
  const { login } = useAuth();
  // --- FIX: Add state for the input fields ---
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const [loginUser, { loading: loginLoading }] = useMutation(LOGIN_MUTATION, {
    onCompleted: (data) => {
      login(data.tokenAuth.token);
      toast.success('Logged in successfully!');
      // Force a full page reload to ensure a clean state
      window.location.href = '/';
    },
    onError: (error) => toast.error(error.message),
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    loginUser({ variables: { username, password } });
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center items-center">
      <div className="max-w-md w-full mx-auto">
        <div className="flex justify-center items-center mb-6">
            <ShieldCheckIcon className="h-12 w-12 text-blue-600"/>
            <h1 className="text-4xl font-bold text-slate-800 ml-3">SyncGrid</h1>
        </div>
        <div className="bg-white p-8 rounded-2xl shadow-lg">
          <h2 className="text-2xl font-bold text-center text-slate-700 mb-1">Welcome!</h2>
          <p className="text-center text-slate-500 mb-6">Please sign in to continue</p>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loginLoading}
              className="w-full mt-6 bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
            >
              {loginLoading ? 'Processing...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
