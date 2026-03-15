import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import Articles from './pages/Articles'
import ArticleDetail from './pages/ArticleDetail'
import BatchManager from './pages/BatchManager'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="companies" element={<Companies />} />
          <Route path="articles" element={<Articles />} />
          <Route path="articles/:id" element={<ArticleDetail />} />
          <Route path="batch" element={<BatchManager />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
