import { useCallback, useEffect, useMemo, useState } from "react";
import reelItInLogo from "./assets/reel-it-in-logo.png";

const API = "http://localhost:8000";
const POLL_MS = 3000;
const LOGO_SRC = reelItInLogo;

const PHASE_CONFIG = {
  TURBULENT: { bg: "#F9D6D6", accent: "#E17777", text: "#9D3F3F", label: "Turbulent" },
  STOP_AND_GO: { bg: "#FFF0C7", accent: "#F0B84B", text: "#96651A", label: "Stop-and-go" },
  LAMINAR: { bg: "#D8EFEB", accent: "#66B7AC", text: "#27766F", label: "Laminar" },
  STATIC: { bg: "#EEF2EF", accent: "#AFC1BC", text: "#67807B", label: "Static" },
};

const tabs = ["Dashboard", "Alerts", "Cameras", "Settings"];

function severity(question = "") {
  const q = question.toLowerCase();
  if (q.includes("turbulent")) return { tag: "Critical", color: "#D86666", bg: "#FBE1E1" };
  if (q.includes("ground") || q.includes("fainted") || q.includes("injured")) {
    return { tag: "High", color: "#D86666", bg: "#FBE1E1" };
  }
  if (q.includes("surrounded") || q.includes("pulsing") || q.includes("bunching")) {
    return { tag: "Medium", color: "#AC7620", bg: "#FFF0C7" };
  }
  return { tag: "Low", color: "#6B8983", bg: "#E9F0ED" };
}

function timeAgo(timestamp, now) {
  const seconds = Math.max(0, Math.floor(now - timestamp));
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s ago`;
}

function camId(path = "") {
  const match = path.match(/(cam\d+)/i);
  return match ? match[1].toUpperCase() : "CAM0";
}

function derivePhase(events, now) {
  const recent = events.filter((event) => now - event.timestamp < 120);
  if (recent.some((event) => event.question?.includes("turbulent") && event.match)) return "TURBULENT";
  if (recent.some((event) => event.question?.includes("pulsing") && event.match)) return "STOP_AND_GO";
  if (recent.length > 0) return "LAMINAR";
  return "STATIC";
}

function formatQuestion(question = "") {
  return question.charAt(0).toUpperCase() + question.slice(1);
}

function Icon({ name, size = 20, stroke = "currentColor" }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke,
    strokeWidth: 1.7,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  const paths = {
    shield: (
      <>
        <path d="M12 3 19 6v5c0 4.5-2.9 8.2-7 10-4.1-1.8-7-5.5-7-10V6l7-3Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    bell: (
      <>
        <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </>
    ),
    camera: (
      <>
        <path d="M4 7h3l1.5-2h7L17 7h3v12H4V7Z" />
        <circle cx="12" cy="13" r="3.3" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    arrow: <path d="M5 12h13m-5-5 5 5-5 5" />,
    arrowUp: <path d="m5 14 7-7 7 7" />,
    arrowDown: <path d="m5 10 7 7 7-7" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    more: <path d="M6 12h.01M12 12h.01M18 12h.01" strokeWidth="2.8" />,
    video: (
      <>
        <rect x="3" y="6" width="13" height="12" rx="2" />
        <path d="m16 10 5-3v10l-5-3" />
      </>
    ),
    eye: (
      <>
        <path d="M2.5 12s3.2-5 9.5-5 9.5 5 9.5 5-3.2 5-9.5 5-9.5-5-9.5-5Z" />
        <circle cx="12" cy="12" r="2.2" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
  };

  return <svg {...common}>{paths[name] || paths.more}</svg>;
}

function Sparkline({ color = "#64AFA5", danger = false }) {
  return (
    <svg viewBox="0 0 116 34" className="sparkline" aria-hidden="true">
      <path
        d={danger ? "M1 23 C10 22 12 22 18 20 S27 20 33 22 S42 24 49 17 S60 15 67 18 S76 10 84 15 S95 11 115 12" : "M1 24 C10 25 14 16 23 20 S33 27 42 22 S52 11 60 16 S70 24 78 17 S91 7 115 10"}
        stroke={color}
        strokeWidth="1.8"
        fill="none"
      />
      <path
        d={danger ? "M1 24 C10 23 12 23 18 21 S27 21 33 23 S42 25 49 18 S60 16 67 19 S76 11 84 16 S95 12 115 13 V34H1Z" : "M1 25 C10 26 14 17 23 21 S33 28 42 23 S52 12 60 17 S70 25 78 18 S91 8 115 11 V34H1Z"}
        fill={color}
        opacity=".12"
      />
    </svg>
  );
}

function RadarGraphic() {
  return (
    <svg viewBox="0 0 150 128" className="radar" aria-hidden="true">
      <g fill="none" stroke="#B8CEC8" strokeWidth="1">
        <path d="M75 12 125 41v57l-50 29-50-29V41L75 12Z" />
        <path d="m75 27 36 21v42L75 111 39 90V48l36-21Z" />
        <path d="m75 41 24 14v28L75 97 51 83V55l24-14Z" />
        <path d="M75 12v57m0 0 50 29M75 69 25 98m50-29-36-21m36 21 36-21" />
      </g>
      <path d="m75 35 31 22-7 35-27 12-32-25 8-29 27-15Z" fill="#B7E2DB" fillOpacity=".65" stroke="#74BEB3" strokeWidth="1.5" />
      <path d="m75 35 0 34m31-12-31 12m24 23-24-23m-32-2 32 2m-24-31 24 29" fill="none" stroke="#74BEB3" strokeWidth="1.2" />
    </svg>
  );
}

function Metric({ label, value, detail, tone = "teal", icon }) {
  return (
    <div className={`metric metric-${tone}`}>
      <div className="metric-icon"><Icon name={icon} size={17} /></div>
      <div>
        <div className="metric-label">{label}</div>
        <div className="metric-value">{value}</div>
        <div className="metric-detail">{detail}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState({});
  const [now, setNow] = useState(Date.now() / 1000);
  const [newQuestion, setNewQuestion] = useState("");
  const [questions, setQuestions] = useState([]);
  const [live, setLive] = useState(false);
  const [navTab, setNavTab] = useState("Dashboard");

  const poll = useCallback(async () => {
    try {
      const [eventsResponse, statsResponse] = await Promise.all([
        fetch(`${API}/api/events?limit=200`),
        fetch(`${API}/api/stats`),
      ]);
      const [eventsData, statsData] = await Promise.all([eventsResponse.json(), statsResponse.json()]);
      setEvents(eventsData.events || []);
      setStats(statsData);
      setNow(statsData.server_time || Date.now() / 1000);
      setLive(true);
    } catch {
      setLive(false);
    }
  }, []);

  useEffect(() => {
    poll();
    const timer = window.setInterval(poll, POLL_MS);
    return () => window.clearInterval(timer);
  }, [poll]);

  useEffect(() => {
    document.title = "Reel-It-In";
    let favicon = document.querySelector('link[rel="icon"]');
    if (!favicon) {
      favicon = document.createElement("link");
      favicon.rel = "icon";
      document.head.appendChild(favicon);
    }
    favicon.type = "image/png";
    favicon.href = LOGO_SRC;
  }, []);

  const passed = useMemo(
    () => events.filter((event) => event.status === "passed").sort((a, b) => b.timestamp - a.timestamp),
    [events],
  );

  const cameras = useMemo(() => {
    const found = [...new Set(events.map((event) => camId(event.chunk_path)))].sort();
    return found.length ? found : ["CAM0", "CAM1", "CAM2"];
  }, [events]);

  const cameraStates = useMemo(
    () => cameras.map((camera) => {
      const cameraEvents = passed.filter((event) => camId(event.chunk_path) === camera);
      const phase = derivePhase(cameraEvents, now);
      const config = PHASE_CONFIG[phase];
      return { camera, cameraEvents, phase, config };
    }),
    [cameras, passed, now],
  );

  const recentAlertCount = stats.total_alerts || passed.length || 0;
  const criticalCount = stats.turbulence_detections || passed.filter((event) => severity(event.question).tag === "Critical").length || 0;
  const reviewCount = stats.review_queue || passed.filter((event) => severity(event.question).tag === "Medium").length || 0;
  const activeCount = 6 + questions.length;

  const submitQuestion = () => {
    if (!newQuestion.trim()) return;
    setQuestions((current) => [...current, newQuestion.trim()]);
    setNewQuestion("");
  };

  return (
    <main className="reel-dashboard">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Marcellus&display=swap');

        :root {
          --ink: #273638;
          --muted: #8a9b98;
          --line: #e7efec;
          --mint: #edf8f6;
          --mint-deep: #d7eeea;
          --gold: #f6b52d;
          --gold-deep: #efa928;
          --teal: #6bb7ac;
          --red: #db7777;
        }

        * { box-sizing: border-box; }
        .reel-dashboard {
          min-height: 100vh;
          padding: 28px;
          color: var(--ink);
          background: #eaf5f3;
          font-family: 'Marcellus', Georgia, serif;
        }
        .dashboard-shell {
          width: min(1180px, 100%);
          margin: 0 auto;
          overflow: hidden;
          border-radius: 44px;
          background: #fff;
          box-shadow: 0 20px 50px rgba(82, 128, 119, .09);
        }
        .hero {
          position: relative;
          min-height: 238px;
          padding: 20px 28px 26px;
          background: #2596be;
        }
        .nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
          min-height: 62px;
          padding: 0 28px;
          border-radius: 36px;
          background: rgba(255,255,255,.97);
        }
        .brand {
          display: inline-flex;
          align-items: center;
          flex: 0 0 auto;
          height: 62px;
          color: #2b3d3c;
          white-space: nowrap;
        }
        .brand-logo {
          display: block;
          width: 92px;
          height: 62px;
          flex: 0 0 auto;
          object-fit: contain;
          object-position: center;
          border-radius: 0;
        }
        .tab-list { display: flex; align-items: center; gap: 6px; }
        .tab {
          border: 0;
          border-radius: 22px;
          padding: 11px 16px;
          color: #aab5b2;
          background: transparent;
          font: 500 11px 'Marcellus', Georgia, serif;
          cursor: pointer;
          transition: .2s ease;
        }
        .tab:hover { color: var(--ink); }
        .tab.active { color: var(--ink); background: #f2f6f3; box-shadow: inset 0 0 0 1px #edf1ef; }
        .hero-content {
          position: relative;
          display: grid;
          grid-template-columns: 1.4fr 1fr 1fr;
          align-items: center;
          gap: 22px;
          max-width: 1015px;
          margin: 26px auto 0;
        }
        .greeting { display: flex; align-items: center; gap: 14px; color: #fff; }
        .avatar {
          display: grid;
          width: 38px;
          height: 38px;
          place-items: center;
          border: 2px solid rgba(255,255,255,.74);
          border-radius: 50%;
          color: #fff;
          background: rgba(255,255,255,.2);
          font-size: 15px;
          font-weight: 700;
        }
        .eyebrow { margin: 0 0 4px; color: rgba(255,255,255,.78); font-size: 11px; }
        .hero-title { margin: 0; font: 700 18px 'Marcellus', Georgia, serif; }
        .hero-copy { max-width: 150px; margin: 0 auto; color: #fff; text-align: center; }
        .hero-copy .small { color: rgba(255,255,255,.76); font-size: 10px; }
        .hero-copy strong { display: block; margin: 5px 0 2px; font: 700 23px 'Marcellus', Georgia, serif; }
        .hero-copy .phase { font-size: 11px; opacity: .82; }
        .wallet { display: flex; align-items: center; justify-content: flex-end; gap: 13px; color: #fff; }
        .wallet-icon { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 50%; color: #fff; background: rgba(255,255,255,.18); }
        .wallet-label { display: block; margin-bottom: 2px; color: rgba(255,255,255,.78); font-size: 9px; text-transform: uppercase; }
        .wallet-value { font: 500 23px 'Marcellus', Georgia, serif; }

        .workspace { padding: 20px 28px 28px; }
        .dashboard-grid {
          display: grid;
          grid-template-columns: 245px minmax(300px, 1fr) 295px;
          gap: 18px;
          align-items: stretch;
          margin-top: 0;
        }
        .column { display: flex; min-width: 0; flex-direction: column; gap: 18px; }
        .card {
          border: 1px solid #edf2ef;
          border-radius: 24px;
          background: #fff;
          box-shadow: 0 7px 24px rgba(80, 116, 108, .045);
        }
        .card-title-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
        .card-title { margin: 0; font: 600 13px 'Marcellus', Georgia, serif; }
        .card-link { display: inline-flex; align-items: center; gap: 4px; color: var(--ink); font-size: 10px; font-weight: 600; }
        .card-link button { display: grid; width: 24px; height: 24px; place-items: center; border: 0; border-radius: 50%; color: inherit; background: #eff7f5; cursor: pointer; }

        .camera-card { min-height: 170px; padding: 21px; background: #a9d8d4; border-color: transparent; }
        .camera-card .card-title { color: #fff; }
        .camera-card .card-link { color: rgba(255,255,255,.94); }
        .camera-card .card-link button { background: rgba(255,255,255,.22); }
        .camera-preview { position: relative; display: grid; height: 78px; margin: 16px 0 9px; place-items: center; overflow: hidden; border-radius: 16px; background: linear-gradient(140deg, rgba(255,255,255,.25), rgba(72,143,136,.16)); }
        .camera-preview::before, .camera-preview::after { content: ''; position: absolute; border: 1px solid rgba(255,255,255,.32); border-radius: 50%; }
        .camera-preview::before { width: 125px; height: 52px; transform: rotate(-16deg); }
        .camera-preview::after { width: 78px; height: 34px; transform: rotate(-16deg); }
        .camera-wave { position: absolute; width: 155px; height: 48px; border-top: 2px solid rgba(255,255,255,.72); border-radius: 50%; transform: rotate(-8deg); }
        .camera-foot { display: flex; align-items: center; justify-content: space-between; color: rgba(255,255,255,.9); font-size: 10px; }
        .live-dot { display: inline-block; width: 7px; height: 7px; margin-right: 5px; border-radius: 50%; background: #ecffcb; box-shadow: 0 0 0 4px rgba(236,255,203,.14); }

        .watch-card { min-height: 140px; padding: 20px; background: #f4dfdf; border-color: transparent; }
        .watch-card .card-title { color: #8e5656; }
        .watch-card p { margin: 11px 0 14px; color: #a86d6d; font-size: 11px; line-height: 1.45; }
        .watch-input { display: flex; gap: 7px; }
        .watch-input input { min-width: 0; flex: 1; border: 1px solid rgba(174,104,104,.25); border-radius: 10px; padding: 8px 10px; outline: none; color: #8b5656; background: rgba(255,255,255,.48); font: 11px 'Marcellus', Georgia, serif; }
        .watch-input input::placeholder { color: #c48d8d; }
        .watch-input button { display: grid; width: 32px; place-items: center; border: 0; border-radius: 10px; color: #fff; background: #d77a7a; cursor: pointer; }
        .question-list { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
        .question-pill { display: inline-flex; align-items: center; gap: 4px; border-radius: 8px; padding: 4px 7px; color: #9b5d5d; background: rgba(255,255,255,.55); font-size: 9px; }
        .question-pill button { padding: 0; border: 0; color: inherit; background: transparent; cursor: pointer; }

        .asset-card { flex: 1; min-height: 190px; padding: 20px; }
        .asset-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; margin: 17px -20px -20px; border-top: 1px solid var(--line); }
        .asset { display: flex; min-height: 117px; flex-direction: column; align-items: center; justify-content: center; gap: 10px; border-right: 1px solid var(--line); color: #627b76; font-size: 10px; }
        .asset:last-child { border-right: 0; }
        .asset-icon { color: #e1b446; }
        .asset-add { display: grid; width: 16px; height: 16px; place-items: center; border-radius: 50%; color: #64a99e; background: #d9f0eb; font-size: 14px; line-height: 1; }

        .overview-card { min-height: 302px; padding: 24px 22px 20px; }
        .overview-head { display: flex; align-items: flex-start; justify-content: space-between; }
        .section-kicker { margin: 0 0 8px; color: #77918b; font-size: 11px; font-weight: 600; }
        .overview-number { margin: 0; font: 700 27px 'Marcellus', Georgia, serif; letter-spacing: -.5px; }
        .overview-tag { color: #59a69b; font-size: 10px; font-weight: 600; }
        .line-chart { width: 100%; height: 166px; margin-top: 9px; }
        .chart-grid { stroke: #e7efec; stroke-width: 1; }
        .chart-area { fill: url(#chartFill); }
        .chart-line { fill: none; stroke: #edb53d; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
        .chart-axis { fill: #a6b6b2; font-size: 9px; }

        .activity-card { flex: 1; padding: 20px 22px; }
        .activity-row { display: flex; align-items: center; gap: 10px; padding: 13px 0; border-bottom: 1px solid #edf2ef; }
        .activity-row:last-child { border-bottom: 0; padding-bottom: 0; }
        .activity-icon { display: grid; width: 27px; height: 27px; place-items: center; border-radius: 50%; color: #6a9891; background: #eaf4f1; }
        .activity-text { min-width: 0; flex: 1; }
        .activity-text strong { display: block; color: #4b615e; font-size: 10px; font-weight: 600; }
        .activity-text span { display: block; margin-top: 3px; color: #9badab; font-size: 9px; }
        .activity-amount { color: #59a69b; font-size: 10px; font-weight: 600; }
        .activity-amount.negative { color: #d47676; }

        .assets-panel { display: grid; grid-template-columns: 1.2fr 1fr; min-height: 218px; overflow: hidden; }
        .asset-summary, .stocks-summary { padding: 20px 18px; }
        .asset-summary { border-right: 1px solid var(--line); }
        .panel-label { margin: 0 0 12px; color: #536b67; font: 600 11px 'Marcellus', Georgia, serif; }
        .radar { display: block; width: 100%; height: 126px; }
        .stocks-summary { background: #fbfdfc; }
        .stocks-value { margin: 28px 0 6px; font: 500 24px 'Marcellus', Georgia, serif; color: #657a76; }
        .stocks-delta { color: #4ca495; font-size: 9px; font-weight: 600; }
        .stocks-delta::before { content: '↗'; padding-right: 3px; }
        .stocks-mini { margin-top: 14px; }

        .alerts-card { flex: 1; min-height: 326px; padding: 20px 18px; }
        .alert-row { display: grid; grid-template-columns: 26px 1fr 80px; align-items: center; gap: 9px; padding: 13px 0; border-bottom: 1px solid var(--line); }
        .alert-row:last-child { border-bottom: 0; }
        .alert-symbol { display: grid; width: 24px; height: 24px; place-items: center; border-radius: 8px; color: #fff; background: #65b6aa; font-size: 11px; font-weight: 700; }
        .alert-symbol.red { background: #e07b7b; }
        .alert-symbol.amber { background: #e6b347; }
        .alert-copy { min-width: 0; }
        .alert-copy strong { display: block; overflow: hidden; color: #536864; font-size: 10px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
        .alert-copy span { display: block; margin-top: 3px; overflow: hidden; color: #9badab; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
        .alert-meta { text-align: right; }
        .alert-meta em { display: block; color: #4ca495; font-size: 9px; font-style: normal; font-weight: 600; }
        .alert-meta small { display: block; margin-top: 3px; color: #a6b6b2; font-size: 8px; }
        .empty-state { padding: 34px 5px; color: #9badab; font-size: 11px; text-align: center; }

        .phase-card { margin-top: 18px; padding: 17px 20px 18px; }
        .phase-card .card-title { color: #6e8983; }
        .phase-row { display: flex; align-items: center; gap: 11px; margin-top: 13px; }
        .phase-label { width: 34px; color: #8fa29e; font-size: 9px; font-weight: 600; }
        .phase-track { display: flex; height: 12px; flex: 1; gap: 2px; overflow: hidden; border-radius: 10px; background: #eff5f3; }
        .phase-segment { flex: 1; }
        .phase-legend { display: flex; flex-wrap: wrap; gap: 17px; margin-top: 14px; color: #8fa29e; font-size: 9px; }
        .legend-item { display: inline-flex; align-items: center; gap: 5px; }
        .legend-dot { width: 8px; height: 8px; border: 1px solid currentColor; border-radius: 3px; }

        .footer-status { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 16px; color: #a1b2ae; font-size: 9px; }
        .status-live { display: inline-flex; align-items: center; gap: 7px; }
        .status-live .live-dot { width: 6px; height: 6px; background: ${live ? "#6fc1ae" : "#d98383"}; box-shadow: none; }

        @media (max-width: 980px) {
          .dashboard-grid { grid-template-columns: 1fr 1fr; }
          .column-center { grid-column: span 2; grid-row: 1; }
          .column-left, .column-right { grid-row: 2; }
          .phase-card { grid-column: span 2; }
        }
        @media (max-width: 680px) {
          .reel-dashboard { padding: 10px; }
          .dashboard-shell { border-radius: 27px; }
          .hero { padding: 12px; }
          .nav { align-items: flex-start; flex-direction: column; gap: 10px; padding: 15px 17px; border-radius: 21px; }
          .tab-list { width: 100%; justify-content: space-between; gap: 2px; overflow-x: auto; }
          .tab { padding: 9px 10px; font-size: 10px; }
          .hero-content { grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 22px; }
          .hero-copy { order: 3; grid-column: span 2; }
          .wallet { justify-content: flex-end; }
          .workspace { padding: 16px 12px 15px; }
          .dashboard-grid { display: flex; flex-direction: column; }
          .column-center { order: 1; }
          .column-left { order: 2; }
          .column-right { order: 3; }
          .phase-card { order: 4; }
          .assets-panel { grid-template-columns: 1fr 1fr; }
        }
      `}</style>

      <section className="dashboard-shell">
        <header className="hero">
          <nav className="nav" aria-label="Primary navigation">
            <div className="brand"><img className="brand-logo" src={LOGO_SRC} alt="Reel-It-In" /></div>
            <div className="tab-list">
              {tabs.map((tab) => (
                <button key={tab} className={`tab ${navTab === tab ? "active" : ""}`} onClick={() => setNavTab(tab)}>
                  {tab}
                </button>
              ))}
            </div>
          </nav>

          <div className="hero-content">
            <div className="greeting">
              <div className="avatar">R</div>
              <div>
                <p className="eyebrow">Good morning,</p>
                <h1 className="hero-title">Crowd safety monitor</h1>
              </div>
            </div>
            <div className="hero-copy">
              <div className="small">CURRENT FLOW</div>
              <strong>{criticalCount ? "Alert mode" : "Clear flow"}</strong>
              <div className="phase">{recentAlertCount} detections in view</div>
            </div>
            <div className="wallet">
              <div className="wallet-icon"><Icon name="shield" size={17} /></div>
              <div><span className="wallet-label">System status</span><span className="wallet-value">{live ? "Live" : "Offline"}</span></div>
            </div>
          </div>
        </header>

        <section className="workspace">
          <div className="dashboard-grid">
            <div className="column column-left">
              <section className="card camera-card">
                <div className="card-title-row">
                  <h2 className="card-title">Live cameras</h2>
                  <span className="card-link">{cameras.length} feeds <button aria-label="Open cameras"><Icon name="arrow" size={14} /></button></span>
                </div>
                <div className="camera-preview"><span className="camera-wave" /><Icon name="video" size={25} stroke="rgba(255,255,255,.9)" /></div>
                <div className="camera-foot"><span><i className="live-dot" />{live ? "Monitoring live" : "Connection paused"}</span><span>HD</span></div>
              </section>

              <section className="card watch-card">
                <div className="card-title-row">
                  <h2 className="card-title">Watch for something new</h2>
                  <span className="card-link"><Icon name="more" size={16} /></span>
                </div>
                <p>Add a plain-language safety question for the next video chunk.</p>
                <div className="watch-input">
                  <input value={newQuestion} onChange={(event) => setNewQuestion(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submitQuestion()} placeholder="anyone climbing the stage" aria-label="New safety question" />
                  <button onClick={submitQuestion} aria-label="Add safety question"><Icon name="plus" size={15} stroke="#fff" /></button>
                </div>
                {questions.length > 0 && <div className="question-list">{questions.map((question, index) => <span className="question-pill" key={`${question}-${index}`}>{question}<button onClick={() => setQuestions((current) => current.filter((_, itemIndex) => itemIndex !== index))} aria-label={`Remove ${question}`}>×</button></span>)}</div>}
              </section>

              <section className="card asset-card">
                <div className="card-title-row"><h2 className="card-title">Safety tools</h2><span className="card-link"><Icon name="more" size={16} /></span></div>
                <div className="asset-grid">
                  {[{ label: "Alerts", icon: "bell" }, { label: "Cameras", icon: "camera" }, { label: "Questions", icon: "eye" }].map((asset) => <div className="asset" key={asset.label}><span className="asset-icon"><Icon name={asset.icon} size={21} /></span><strong>{asset.label}</strong><span className="asset-add"><Icon name="plus" size={11} /></span></div>)}
                </div>
              </section>
            </div>

            <div className="column column-center">
              <section className="card overview-card">
                <div className="overview-head"><div><p className="section-kicker">Detected activity</p><h2 className="overview-number">{recentAlertCount} <span style={{ fontSize: 12, fontWeight: 500, color: "#8da19c" }}>alerts</span></h2></div><span className="overview-tag">Last 10 min <Icon name="arrowUp" size={12} /></span></div>
                <svg className="line-chart" viewBox="0 0 390 166" preserveAspectRatio="none" aria-label="Detected activity chart">
                  <defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#F5C65D" stopOpacity=".48" /><stop offset="1" stopColor="#F5C65D" stopOpacity="0" /></linearGradient></defs>
                  {[28, 65, 102, 139].map((y) => <line key={y} x1="31" y1={y} x2="384" y2={y} className="chart-grid" />)}
                  <text x="0" y="31" className="chart-axis">high</text><text x="0" y="68" className="chart-axis">med</text><text x="0" y="105" className="chart-axis">low</text>
                  <path className="chart-area" d="M32 139 C49 141 57 116 69 119 S87 77 107 84 S125 62 139 64 S156 26 177 31 S191 64 211 61 S227 104 246 92 S269 80 282 89 S304 59 321 73 S346 93 361 78 S376 73 384 79 V148 H32Z" />
                  <path className="chart-line" d="M32 139 C49 141 57 116 69 119 S87 77 107 84 S125 62 139 64 S156 26 177 31 S191 64 211 61 S227 104 246 92 S269 80 282 89 S304 59 321 73 S346 93 361 78 S376 73 384 79" />
                  <text x="30" y="162" className="chart-axis">10m ago</text><text x="350" y="162" className="chart-axis">now</text>
                </svg>
              </section>

              <section className="card activity-card">
                <div className="card-title-row"><h2 className="card-title">Recent activity</h2><span className="card-link">View all <button aria-label="View all activity"><Icon name="arrow" size={14} /></button></span></div>
                {passed.length === 0 ? <div className="empty-state">Waiting for the first processed chunk…</div> : passed.slice(0, 3).map((event, index) => <div className="activity-row" key={`${event.id || event.timestamp}-${index}`}><div className="activity-icon"><Icon name={index === 0 ? "eye" : "clock"} size={14} /></div><div className="activity-text"><strong>{formatQuestion(event.question)}</strong><span>{camId(event.chunk_path)} · {timeAgo(event.timestamp, now)}</span></div><span className={`activity-amount ${severity(event.question).tag === "Critical" ? "negative" : ""}`}>{severity(event.question).tag === "Critical" ? "Review" : "Logged"}</span></div>)}
              </section>
            </div>

            <div className="column column-right">
              <section className="card assets-panel">
                <div className="asset-summary"><h2 className="panel-label">Your coverage</h2><RadarGraphic /></div>
                <div className="stocks-summary"><h2 className="panel-label">Safety score</h2><div className="stocks-value">{Math.max(0, 100 - criticalCount * 8 - reviewCount * 2)}%</div><div className="stocks-delta">+12.3% / month</div><div className="stocks-mini"><Sparkline /></div></div>
              </section>

              <section className="card alerts-card">
                <div className="card-title-row"><h2 className="card-title">Needs attention</h2><span className="card-link">All alerts <button aria-label="View all alerts"><Icon name="arrow" size={14} /></button></span></div>
                {passed.length === 0 ? <div className="empty-state">No alerts yet. Processed detections will appear here.</div> : passed.slice(0, 4).map((event, index) => { const level = severity(event.question); return <div className="alert-row" key={`${event.id || event.timestamp}-${index}`}><span className={`alert-symbol ${level.tag === "Critical" || level.tag === "High" ? "red" : level.tag === "Medium" ? "amber" : ""}`}>{level.tag === "Critical" ? "!" : level.tag === "High" ? "↑" : "•"}</span><div className="alert-copy"><strong>{formatQuestion(event.question)}</strong><span>{camId(event.chunk_path)} · {timeAgo(event.timestamp, now)}</span></div><div className="alert-meta"><em>{level.tag}</em><small>Review</small></div></div>; })}
              </section>
            </div>
          </div>

          <section className="card phase-card">
            <div className="card-title-row"><h2 className="card-title">Phase history · last 10 min</h2><span className="card-link"><Icon name="more" size={16} /></span></div>
            {cameraStates.map(({ camera, cameraEvents }) => <div className="phase-row" key={camera}><span className="phase-label">{camera}</span><div className="phase-track">{cameraEvents.length === 0 ? <div className="phase-segment" style={{ background: PHASE_CONFIG.STATIC.bg }} /> : cameraEvents.slice(-18).map((event, index) => { let phase = "STATIC"; if (event.question?.includes("turbulent") && event.match) phase = "TURBULENT"; else if (event.question?.includes("pulsing") && event.match) phase = "STOP_AND_GO"; else if (event.match) phase = "LAMINAR"; return <div className="phase-segment" key={`${event.timestamp}-${index}`} style={{ background: PHASE_CONFIG[phase].bg }} />; })}</div></div>)}
            <div className="phase-legend">{["LAMINAR", "STOP_AND_GO", "TURBULENT"].map((phase) => <span className="legend-item" key={phase}><i className="legend-dot" style={{ color: PHASE_CONFIG[phase].accent, background: PHASE_CONFIG[phase].bg }} />{PHASE_CONFIG[phase].label}</span>)}</div>
          </section>

          <footer className="footer-status"><span>{activeCount} active safety questions · Updates every 3 seconds</span><span className="status-live"><i className="live-dot" />{live ? "System live" : "Waiting for API"}</span></footer>
        </section>
      </section>
    </main>
  );
}

export { PHASE_CONFIG, derivePhase, severity, timeAgo };


