import { Routes, Route } from 'react-router-dom'
import { Home } from '@/pages/Home'
import { AIGame } from '@/pages/AIGame'
import { MultiplayerGame } from '@/pages/MultiplayerGame'
import { Layout } from '@/components/Layout'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/ai" element={<AIGame />} />
        <Route path="/multiplayer" element={<MultiplayerGame />} />
      </Routes>
    </Layout>
  )
}

export default App 