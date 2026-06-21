# LLM Output

=== FILE: src/main.jsx ===
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
=== END ===
=== FILE: src/index.css ===
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar for a premium feel */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #1e293b; /* Dark slate */
  border-radius: 10px;
}
::-webkit-scrollbar-thumb {
  background: #475569; /* Slate */
  border-radius: 10px;
  transition: background 0.3s ease;
}
::-webkit-scrollbar-thumb:hover {
  background: #64748b; /* Lighter slate */
}

/* Base styles for dark mode */
body {
  @apply bg-gradient-to-br from-slate-950 to-indigo-950 text-gray-100 font-sans;
  min-height: 100vh;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#root {
  min-height: 100vh;
}
=== END ===
=== FILE: src/api.js ===
import axios from 'axios';

// CRITICAL: DO NOT hardcode Render, Railway, or any deployment URLs.
export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
=== END ===
=== FILE: src/App.jsx ===
import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { HashRouter, Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import toast, { Toaster } from 'react-hot-toast';
import { DollarSign, Tag, Calendar, Home, LogOut, PlusCircle, LayoutDashboard, Wallet, TrendingUp, TrendingDown, BookOpen, CreditCard, Utensils, Car, Bill, Gift, PiggyBank, Search } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import clsx from 'clsx';
import api from './api'; // Approved: import from api.js

// CRITICAL: App.jsx MUST be completely self-contained. No local component imports.
// All sub-components are defined within the App function or globally if truly simple helpers.

// --- Helper Functions and Constants ---
const categoryColors = {
  Food: 'text-green-400 bg-green-500/20',
  Transport: 'text-blue-400 bg-blue-500/20',
  Bills: 'text-red-400 bg-red-500/20',
  Entertainment: 'text-purple-400 bg-purple-500/20',
  Subscription: 'text-indigo-400 bg-indigo-500/20',
  Other: 'text-gray-400 bg-gray-500/20',
};

const categoryIcons = {
  Food: <Utensils size={16} />,
  Transport: <Car size={16} />,
  Bills: <Bill size={16} />,
  Entertainment: <Gift size={16} />,
  Subscription: <CreditCard size={16} />,
  Other: <BookOpen size={16} />,
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
};

// Authentication Context
const AuthContext = createContext(null);

// --- Main App Component ---
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const navigate = useNavigate();

  // Effect to set Axios auth header when token changes
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setIsAuthenticated(true);
      // Try to fetch user data to verify token
      api.get('/api/user/me')
        .then(response => {
          if (response.data && response.data.username) {
            setUser(response.data);
          } else {
            handleLogout(); // Token invalid or user data missing
          }
        })
        .catch(() => {
          handleLogout();
        });
    } else {
      delete api.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
      setUser(null);
    }
  }, [token]);

  // Handle successful login
  const handleLogin = useCallback((authToken, userData) => {
    localStorage.setItem('authToken', authToken);
    setToken(authToken);
    setUser(userData);
    setIsAuthenticated(true);
    toast.success('Login successful!');
    navigate('/');
  }, [navigate]);

  // Handle logout
  const handleLogout = useCallback(() => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    toast('Logged out successfully!', { icon: '👋' });
    navigate('/login');
  }, [navigate]);

  // --- Internal Components Definition ---

  // 1. Login Screen
  const LoginScreen = ({ onLoginSuccess }) => {
    const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
    const [loginError, setLoginError] = useState('');

    const onSubmit = async (data) => {
      setLoginError('');
      try {
        const response = await api.post('/api/auth/login', data);
        if (response.data && response.data.access_token) {
          // Assuming the backend returns a user object along with the token
          // For this MVP, let's mock user data if not provided directly
          const userData = { username: data.username, id: 'user-123' };
          onLoginSuccess(response.data.access_token, userData);
        } else {
          setLoginError('Invalid response from server.');
        }
      } catch (err) {
        setLoginError(err.response?.data?.detail || 'Login failed. Please try again.');
        toast.error('Login failed!');
      }
    };

    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="relative w-full max-w-md bg-gradient-to-br from-indigo-900/40 to-purple-900/40 backdrop-blur-xl border border-indigo-700/30 rounded-2xl shadow-2xl p-8 transition-all duration-300 transform hover:scale-[1.01]">
          <div className="flex flex-col items-center mb-8">
            <PiggyBank className="w-16 h-16 text-teal-400 mb-4 animate-bounce-slow" />
            <h1 className="text-4xl font-extrabold text-white text-center tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-emerald-500">
              Expense Tracker
            </h1>
            <p className="text-gray-400 mt-2 text-center">Login to manage your finances</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">Username</label>
              <div className="relative">
                <input
                  id="username"
                  type="text"
                  {...register('username', { required: 'Username is required' })}
                  className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-teal-500 focus:border-teal-500 transition-all duration-300"
                  placeholder="john.doe"
                />
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              </div>
              {errors.username && <p className="mt-2 text-sm text-red-400">{errors.username.message}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type="password"
                  {...register('password', { required: 'Password is required' })}
                  className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-teal-500 focus:border-teal-500 transition-all duration-300"
                  placeholder="••••••••"
                />
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              </div>
              {errors.password && <p className="mt-2 text-sm text-red-400">{errors.password.message}</p>}
            </div>

            {loginError && (
              <p className="text-red-400 text-sm text-center bg-red-900/30 p-2 rounded-md border border-red-700/50">
                {loginError}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:from-teal-600 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <span className="animate-spin h-5 w-5 mr-3 border-b-2 border-white rounded-full"></span>
                  Logging in...
                </span>
              ) : (
                <>
                  <LogIn className="mr-2" size={20} /> Login
                </>
              )}
            </button>
          </form>
          <p className="mt-8 text-center text-gray-400 text-sm">
            Don't have an account? <a href="#" className="text-teal-400 hover:underline">Sign Up</a>
          </p>
        </div>
      </div>
    );
  };

  // 2. Dashboard Screen
  const DashboardScreen = ({ user, token, onLogout }) => {
    const [expenses, setExpenses] = useState([]);
    const [kpis, setKpis] = useState({
      totalBalance: 0,
      monthlySpend: 0,
      largestExpense: 0,
      activeSubscriptions: 0,
    });
    const [loadingExpenses, setLoadingExpenses] = useState(true);
    const [loadingKpis, setLoadingKpis] = useState(true);
    const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('All');

    const fetchExpenses = useCallback(async () => {
      setLoadingExpenses(true);
      try {
        const response = await api.get('/api/expenses');
        const safeData = Array.isArray(response.data) ? response.data : (response.data?.items || []);
        setExpenses(safeData);
      } catch (error) {
        toast.error('Failed to fetch expenses.');
        console.error('Fetch expenses error:', error);
        // CRITICAL DATA SAFETY: Ensure expenses is an array even on error
        setExpenses([]);
      } finally {
        setLoadingExpenses(false);
      }
    }, [token]);

    const fetchKpis = useCallback(async () => {
      setLoadingKpis(true);
      try {
        const response = await api.get('/api/dashboard/summary');
        if (response.data) {
          setKpis({
            totalBalance: response.data.total_balance || 0,
            monthlySpend: response.data.monthly_spend || 0,
            largestExpense: response.data.largest_expense || 0,
            activeSubscriptions: response.data.active_subscriptions || 0,
          });
        }
      } catch (error) {
        toast.error('Failed to fetch KPI data.');
        console.error('Fetch KPIs error:', error);
        setKpis({ totalBalance: 0, monthlySpend: 0, largestExpense: 0, activeSubscriptions: 0 });
      } finally {
        setLoadingKpis(false);
      }
    }, [token]);

    useEffect(() => {
      fetchExpenses();
      fetchKpis();
    }, [fetchExpenses, fetchKpis]);

    const handleAddExpense = useCallback(async (newExpenseData) => {
      try {
        await api.post('/api/expenses', newExpenseData);
        toast.success('Expense added successfully!');
        fetchExpenses(); // Re-fetch expenses to update the list
        fetchKpis(); // Re-fetch KPIs to update metrics
      } catch (error) {
        toast.error('Failed to add expense.');
        console.error('Add expense error:', error);
      }
    }, [fetchExpenses, fetchKpis]);

    // 2.1. Sidebar Component
    const Sidebar = ({ currentUser, onLogout: handleLogoutClick }) => {
      const navItems = [
        { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, path: '/' },
        { name: 'Expenses', icon: <DollarSign className="w-5 h-5" />, path: '/expenses' }, // Could be a separate page later
        // { name: 'Reports', icon: <BarChart className="w-5 h-5" />, path: '/reports' },
      ];

      return (
        <aside className="hidden lg:flex flex-col w-64 h-full fixed top-0 left-0 bg-gradient-to-br from-indigo-900/30 to-purple-900/30 backdrop-blur-xl border-r border-indigo-700/30 p-6 shadow-xl z-30">
          <div className="flex items-center justify-center mb-10 mt-2">
            <PiggyBank className="w-10 h-10 text-teal-400 mr-3" />
            <span className="text-3xl font-extrabold text-white bg-clip-text text-transparent bg-gradient-to-r from-teal-300 to-emerald-400">
              Expensify
            </span>
          </div>
          <nav className="flex-grow space-y-4">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className="flex items-center px-4 py-3 rounded-xl text-gray-200 hover:bg-white/10 hover:text-white transition-all duration-200 group relative overflow-hidden"
              >
                <span className="absolute inset-0 bg-teal-500 opacity-0 group-hover:opacity-10 transition-opacity duration-200 z-0"></span>
                <span className="z-10 flex items-center">
                  {item.icon}
                  <span className="ml-4 text-lg font-medium">{item.name}</span>
                </span>
              </Link>
            ))}
          </nav>
          <div className="mt-auto pt-6 border-t border-indigo-700/30">
            {currentUser && (
              <div className="flex items-center p-4 rounded-lg bg-white/10 border border-white/20 mb-4">
                <div className="w-10 h-10 bg-teal-500 rounded-full flex items-center justify-center text-white font-bold text-lg mr-3">
                  {currentUser.username ? currentUser.username.charAt(0).toUpperCase() : 'U'}
                </div>
                <div className="flex-grow">
                  <span className="block text-white font-semibold">{currentUser.username || 'User'}</span>
                  <span className="block text-gray-400 text-sm">Premium Member</span>
                </div>
              </div>
            )}
            <button
              onClick={handleLogoutClick}
              className="w-full flex items-center justify-center px-4 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-all duration-300 shadow-md transform hover:scale-[1.01]"
            >
              <LogOut className="w-5 h-5 mr-3" />
              Logout
            </button>
          </div>
        </aside>
      );
    };

    // 2.2. KPI Cards Component
    const KPICards = ({ kpiData, loading }) => {
      const kpiItems = [
        {
          label: 'Total Net Spend',
          value: formatCurrency(kpiData.totalBalance),
          icon: <Wallet className="text-pink-400" />,
          trend: <TrendingDown className="text-red-400" size={20} />,
          description: 'Overall expenses to date',
        },
        {
          label: 'Monthly Spend',
          value: formatCurrency(kpiData.monthlySpend),
          icon: <BookOpen className="text-teal-400" />,
          trend: <TrendingDown className="text-red-400" size={20} />,
          description: 'This month\'s expenses',
        },
        {
          label: 'Largest Expense',
          value: formatCurrency(kpiData.largestExpense),
          icon: <DollarSign className="text-orange-400" />,
          trend: <TrendingUp className="text-green-400" size={20} />,
          description: 'Biggest single transaction',
        },
        {
          label: 'Active Subscriptions',
          value: kpiData.activeSubscriptions,
          icon: <CreditCard className="text-purple-400" />,
          trend: null, // No trend for count
          description: 'Recurring payments',
        },
      ];

      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {kpiItems.map((item, index) => (
            <div
              key={index}
              className="relative bg-gradient-to-br from-indigo-800/20 to-purple-800/20 backdrop-blur-xl border border-indigo-700/20 rounded-2xl p-6 shadow-xl transition-all duration-300 hover:scale-[1.02] transform group overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-tr from-teal-500/10 to-transparent opacity-0 group-hover:opacity-10 transition-opacity duration-300 z-0"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <div className="bg-white/10 p-3 rounded-full border border-white/20">
                    {item.icon}
                  </div>
                  {item.trend && <div className="p-1 rounded-full">{item.trend}</div>}
                </div>
                <p className="text-gray-300 text-sm font-medium">{item.label}</p>
                {loading ? (
                  <div className="h-8 w-3/4 bg-gray-700 rounded animate-pulse mt-2"></div>
                ) : (
                  <h2 className="text-3xl font-bold text-white mt-2 bg-clip-text text-transparent bg-gradient-to-r from-teal-300 to-emerald-400">
                    {item.value}
                  </h2>
                )}
                <p className="text-gray-500 text-xs mt-1">{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      );
    };

    // 2.3. Add Expense Form Component
    const AddExpenseForm = ({ onAddExpense }) => {
      const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm({
        defaultValues: {
          description: '',
          amount: '',
          category: 'Food',
          date: format(new Date(), 'yyyy-MM-dd'),
        },
      });

      const onSubmit = async (data) => {
        try {
          await onAddExpense({
            ...data,
            amount: parseFloat(data.amount),
          });
          reset({
            description: '',
            amount: '',
            category: 'Food',
            date: format(new Date(), 'yyyy-MM-dd'),
          });
        } catch (error) {
          // Error handled in parent onAddExpense
        }
      };

      const categories = ['Food', 'Transport', 'Bills', 'Entertainment', 'Subscription', 'Other'];

      return (
        <div className="bg-gradient-to-br from-gray-800/30 to-gray-900/30 backdrop-blur-xl border border-gray-700/20 rounded-2xl p-6 shadow-xl mb-8 transition-all duration-300 hover:scale-[1.005]">
          <h3 className="text-2xl font-semibold text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-emerald-300 to-teal-400">Quick Add Expense</h3>
          <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="col-span-1 md:col-span-2">
              <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <input
                id="description"
                type="text"
                {...register('description', { required: 'Description is required' })}
                className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-teal-500 focus:border-teal-500 transition-all duration-300"
                placeholder="Groceries from supermarket"
              />
              {errors.description && <p className="mt-1 text-sm text-red-400">{errors.description.message}</p>}
            </div>
            <div>
              <label htmlFor="amount" className="block text-sm font-medium text-gray-300 mb-2">Amount ($)</label>
              <input
                id="amount"
                type="number"
                step="0.01"
                {...register('amount', { required: 'Amount is required', min: { value: 0.01, message: 'Amount must be positive' } })}
                className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-teal-500 focus:border-teal-500 transition-all duration-300"
                placeholder="25.50"
              />
              {errors.amount && <p className="mt-1 text-sm text-red-400">{errors.amount.message}</p>}
            </div>
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-300 mb-2">Category</label>
              <select
                id="category"
                {...register('category', { required: 'Category is required' })}
                className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:ring-teal-500 focus:border-teal-500 transition-all duration-300"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              {errors.category && <p className="mt-1 text-sm text-red-400">{errors.category.message}</p>}
            </div>
            <div>
              <label htmlFor="date" className="block text-sm font-medium text-gray-300 mb-2">Date</label>
              <input
                id="date"
                type="date"
                {...register('date', { required: 'Date is required' })}
                className="w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:ring-teal-500 focus:border-teal-500 transition-all duration-300"
              />
              {errors.date && <p className="mt-1 text-sm text-red-400">{errors.date.message}</p>}
            </div>
            <div className="col-span-full flex justify-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-bold py-2 px-6 rounded-lg shadow-md hover:from-teal-600 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isSubmitting ? (
                  <span className="flex items-center">
                    <span className="animate-spin h-5 w-5 mr-3 border-b-2 border-white rounded-full"></span>
                    Adding...
                  </span>
                ) : (
                  <>
                    <PlusCircle className="mr-2" size={20} /> Add Expense
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      );
    };

    // 2.4. Transactions List Component
    const TransactionsList = ({ transactions, loading, selectedFilter, onSelectFilter }) => {
      const allCategories = ['All', ...new Set(transactions.map(t => t.category))].filter(Boolean); // Ensure no null/undefined

      const filteredTransactions = selectedFilter === 'All'
        ? transactions
        : transactions.filter(t => t.category === selectedFilter);

      return (
        <div className="bg-gradient-to-br from-gray-800/30 to-gray-900/30 backdrop-blur-xl border border-gray-700/20 rounded-2xl p-6 shadow-xl">
          <h3 className="text-2xl font-semibold text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-emerald-300 to-teal-400">Past Transactions</h3>

          <div className="mb-6 flex flex-wrap gap-2">
            {allCategories.map(category => (
              <button
                key={category}
                onClick={() => onSelectFilter(category)}
                className={clsx(
                  "px-4 py-2 rounded-full text-sm font-medium transition-all duration-300",
                  selectedFilter === category
                    ? "bg-teal-600 text-white shadow-md transform scale-105"
                    : "bg-gray-700/50 text-gray-300 hover:bg-gray-600/70 hover:text-white"
                )}
              >
                {category}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-700/50 rounded animate-pulse"></div>
                ))}
              </div>
            ) : filteredTransactions.length === 0 ? (
              <p className="text-gray-400 text-center p-8 text-lg">No transactions found. Add a new expense above!</p>
            ) : (
              <table className="min-w-full table-auto border-collapse">
                <thead>
                  <tr className="bg-gray-700/60 text-gray-300">
                    <th className="py-3 px-4 text-left font-medium rounded-tl-xl">Description</th>
                    <th className="py-3 px-4 text-left font-medium">Category</th>
                    <th className="py-3 px-4 text-left font-medium">Date</th>
                    <th className="py-3 px-4 text-right font-medium rounded-tr-xl">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTransactions.map((transaction, index) => (
                    <tr
                      key={transaction.id || index}
                      className="border-t border-gray-700 hover:bg-white/5 transition-all duration-200 group"
                    >
                      <td className="py-3 px-4 text-gray-200">
                        {transaction.description}
                      </td>
                      <td className="py-3 px-4">
                        <span className={clsx(
                          "inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold",
                          categoryColors[transaction.category] || 'text-gray-400 bg-gray-500/20'
                        )}>
                          {categoryIcons[transaction.category]}
                          {transaction.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-300">
                        {transaction.date ? format(parseISO(transaction.date), 'MMM dd, yyyy') : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-right font-medium text-red-400">
                        {formatCurrency(transaction.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      );
    };

    return (
      <div className="flex min-h-screen">
        <Sidebar currentUser={user} onLogout={onLogout} />
        <main className="flex-grow lg:ml-64 p-8 pt-10 relative z-10">
          <header className="mb-10">
            <h1 className="text-5xl font-extrabold text-white mb-2 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-teal-300 to-emerald-400">
              Welcome, {user?.username || 'User'}!
            </h1>
            <p className="text-gray-400 text-lg">
              Here's your financial overview and quick expense management.
            </p>
          </header>

          <KPICards kpiData={kpis} loading={loadingKpis} />
          <AddExpenseForm onAddExpense={handleAddExpense} />
          <TransactionsList
            transactions={expenses}
            loading={loadingExpenses}
            selectedFilter={selectedCategoryFilter}
            onSelectFilter={setSelectedCategoryFilter}
          />
        </main>
      </div>
    );
  };

  // --- Main App Routing ---
  return (
    <AuthContext.Provider value={{ isAuthenticated, user, token, handleLogin, handleLogout }}>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#334155', // Slate-700
            color: '#cbd5e1', // Slate-300
            border: '1px solid #475569', // Slate-600
            backdropFilter: 'blur(10px)',
          },
        }}
      />
      <HashRouter>
        <Routes>
          <Route path="/login" element={<LoginScreen onLoginSuccess={handleLogin} />} />
          <Route
            path="/*"
            element={isAuthenticated ? <DashboardScreen user={user} token={token} onLogout={handleLogout} /> : <Navigate to="/login" />}
          />
        </Routes>
      </HashRouter>
    </AuthContext.Provider>
  );
}

// Ensure all Lucide icons are imported and used to avoid errors if not included earlier
const User = ({ size, className }) => <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>;
const Lock = ({ size, className }) => <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>;
const LogIn = ({ size, className }) => <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" x2="3" y1="12" y2="12"/></svg>;

// Export App as default
export default App;
=== END ===