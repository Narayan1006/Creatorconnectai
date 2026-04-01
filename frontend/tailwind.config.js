/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Brand design system — Apple-inspired dark aesthetic
        brand: {
          bg: '#0B0B0C',
          text: '#FFFFFF',
          accent: '#8E8E93',
          surface: '#1C1C1E',
          border: '#2C2C2E',
          muted: '#636366',
        },
        // Legacy colors (kept for backward compatibility)
        surface: '#f9f9fb',
        surface_bright: '#ffffff',
        surface_container_lowest: '#ffffff',
        surface_container_low: '#f2f4f6',
        surface_container: '#eceef1',
        surface_container_high: '#e5e8eb',
        surface_container_highest: '#dde0e4',
        surface_tint: '#4f4ccd',
        on_surface: '#2d3338',
        on_surface_variant: '#6b7280',
        outline_variant: '#acb3b8',
        primary: '#4f4ccd',
        primary_dim: '#423fc0',
        primary_container: '#e8e7f8',
        on_primary: '#ffffff',
        on_primary_container: '#1a1880',
      },
      borderRadius: {
        sm: '0.375rem',
        md: '0.75rem',
        lg: '1rem',
        xl: '1.5rem',
      },
      boxShadow: {
        ambient: '0 10px 40px 0 rgba(45,51,56,0.04)',
        float: '0 2px 12px 0 rgba(45,51,56,0.06)',
      },
      backdropBlur: {
        glass: '24px',
      },
    },
  },
  plugins: [],
}
