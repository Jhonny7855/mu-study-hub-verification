import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import AdminDashboard from './pages/AdminDashboard';
import StudentUploadPage from './pages/StudentUpload';

function App() {
  return (
    <BrowserRouter>
      <nav className="bg-blue-600 text-white px-4 py-3">
        <div className="max-w-4xl mx-auto flex gap-4">
          <NavLink
            to="/"
            className={({ isActive }) => isActive ? 'underline' : ''}
          >
            Student Upload
          </NavLink>
          <NavLink
            to="/admin"
            className={({ isActive }) => isActive ? 'underline' : ''}
          >
            Admin Dashboard
          </NavLink>
        </div>
      </nav>

      <main className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<StudentUploadPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;