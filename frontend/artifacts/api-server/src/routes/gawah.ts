/**
 * Gawah API stub routes
 *
 * These routes mirror the FastAPI contract consumed by the Gawah frontend
 * (artifacts/gawah-frontend/src/lib/api.ts). They return well-typed empty/demo
 * responses so the UI is fully functional when VITE_API_URL points at this
 * Express server instead of the Python backend.
 *
 * Route contract (matches frontend fetch helpers):
 *   POST /api/sessions/create
 *   GET  /api/dashboard/statements
 *   GET  /api/statements/:refCode
 *   POST /api/statements/:refCode/review
 *   GET  /api/statements/:refCode/audio   → 404 (no audio in stub)
 *   POST /api/statements/:refCode/pdf     → 404 (no PDF in stub)
 *   GET  /api/kpis
 *   GET  /api/dashboard/clusters
 *   GET  /api/dashboard/clusters/:clusterId
 */

import { Router, type IRouter } from "express";

const router: IRouter = Router();

// ── Sessions ──────────────────────────────────────────────────────────────

router.post("/sessions/create", (_req, res) => {
  res.json({
    room_name: `room-${Math.random().toString(36).slice(2, 8)}`,
    token: `demo-token-${Date.now()}`,
    ws_url: "wss://demo.livekit.example/",
    demo: true,
    ok: true,
  });
});

// ── KPIs ──────────────────────────────────────────────────────────────────

router.get("/kpis", (_req, res) => {
  res.json({
    total_statements: 0,
    urgent_count: 0,
    cluster_count: 0,
    avg_corroboration: null,
  });
});

// ── Statements list ────────────────────────────────────────────────────────

router.get("/dashboard/statements", (_req, res) => {
  res.json({
    items: [],
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 0,
  });
});

// ── Statement detail ───────────────────────────────────────────────────────

router.get("/statements/:refCode", (req, res) => {
  res.status(404).json({
    detail: `Statement ${req.params.refCode} not found. Connect the FastAPI backend or seed the database.`,
  });
});

router.post("/statements/:refCode/review", (req, res) => {
  res.status(404).json({
    detail: `Statement ${req.params.refCode} not found.`,
  });
});

router.get("/statements/:refCode/audio", (_req, res) => {
  res.status(404).json({ detail: "Audio not available in stub mode." });
});

router.post("/statements/:refCode/pdf", (_req, res) => {
  res.status(404).json({ detail: "PDF export not available in stub mode." });
});

// ── Clusters ──────────────────────────────────────────────────────────────

router.get("/dashboard/clusters", (_req, res) => {
  res.json({ items: [], total: 0 });
});

router.get("/dashboard/clusters/:clusterId", (req, res) => {
  res.status(404).json({
    detail: `Cluster ${req.params.clusterId} not found.`,
  });
});

export default router;
