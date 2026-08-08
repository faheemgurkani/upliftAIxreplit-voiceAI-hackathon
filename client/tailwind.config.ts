import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a1210",
          900: "#0f1c18",
          800: "#152821",
          700: "#1e3a2f",
          600: "#2a4f40",
        },
        moss: {
          400: "#6f9b7a",
          500: "#4f7d5c",
          600: "#3a6348",
        },
        brass: {
          300: "#e2c07a",
          400: "#d4a84b",
          500: "#b8892e",
        },
        mist: {
          50: "#f3f6f4",
          100: "#e4ebe6",
          200: "#c8d5cc",
          400: "#8a9e90",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.45" },
          "50%": { opacity: "0.85" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
      },
      animation: {
        "fade-up": "fadeUp 0.7s ease-out both",
        "fade-up-delay": "fadeUp 0.7s ease-out 0.15s both",
        "fade-up-late": "fadeUp 0.7s ease-out 0.3s both",
        "pulse-soft": "pulseSoft 4s ease-in-out infinite",
        shimmer: "shimmer 3s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
