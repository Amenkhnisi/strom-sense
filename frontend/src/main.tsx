import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import App from './App.tsx'
import BillInput from './components/BillInput.tsx';



const router = createBrowserRouter([
  {
    path: "/", element: <App />,
    children: [{
      path: "Bill-Input", element: <BillInput />

    }]
  }

])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
