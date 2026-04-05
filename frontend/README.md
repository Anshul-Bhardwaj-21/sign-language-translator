# Frontend - Sign Language Video Call

React + TypeScript frontend for the sign language accessible video meeting system.

## Quick Start

```bash
# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Open browser
http://localhost:3000
```

## Available Scripts

- `npm run dev` - Start development server (hot reload)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── pages/              # Page components
│   ├── LandingPage.tsx
│   ├── PreJoinLobby.tsx
│   └── VideoCallPage.tsx
├── services/           # API and services
│   ├── api.ts
│   └── FrameCaptureManager.ts
├── styles/             # Global styles
│   └── index.css
├── App.tsx             # Main app with routing
└── main.tsx            # Entry point
```

## Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Socket.IO** - WebSocket client

## Development

### Hot Reload

The dev server supports hot module replacement (HMR). Changes to React components will update instantly without page refresh.

### TypeScript

All files use TypeScript for type safety. The compiler will catch errors before runtime.

### Tailwind CSS

Use Tailwind utility classes for styling:

```tsx
<div className="bg-gray-900 text-white p-4 rounded-lg">
  Content
</div>
```

## Building for Production

```bash
npm run build
```

Output will be in `dist/` directory. Serve with any static file server.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

WebRTC requires modern browsers with camera/microphone support.

## Troubleshooting

### Port 3000 in use

Change port in `vite.config.ts`:

```ts
server: {
  port: 3001
}
```

### Module not found

```bash
rm -rf node_modules package-lock.json
npm install
```

### TypeScript errors

```bash
npm run build
```

This will show all TypeScript errors.

