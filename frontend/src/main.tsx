import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import "./styles/custom-bootstrap.scss"
import App from './App.tsx'
import { ConfigProvider } from './context/ConfigProvider';

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <ConfigProvider>
            <App />
        </ConfigProvider>
    </StrictMode>,
)
