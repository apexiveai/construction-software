import React from "react";
import { createRoot } from "react-dom/client";
import { apiRequest } from "./api.js";
import "./styles.css";

const modules = [
  { id: "bim", label: "3D BIM + Digital Twin", short: "Digital twin", icon: "cube" },
  { id: "copilot", label: "AI Construction Copilot", short: "AI copilot", icon: "spark" },
  { id: "safety", label: "Safety AI Monitoring", short: "Safety AI", icon: "shield" },
  { id: "cost", label: "Cost & Budget Analytics", short: "Cost analytics", icon: "chart" },
  { id: "risk", label: "Delay / Risk Prediction", short: "Risk prediction", icon: "warning" },
  { id: "procurement", label: "Procurement Management", short: "Procurement", icon: "truck" },
  { id: "quality", label: "Quality Inspection", short: "Quality", icon: "check" },
  { id: "equipment", label: "Equipment IoT Tracking", short: "Equipment IoT", icon: "crane" },
];

function Icon({ name, size = 18 }) {
  const paths = {
    cube: <><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4.3 7.7 7.7 4.5 7.7-4.5M12 21v-8.8M8 5.3l8 4.6" /></>,
    spark: <><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /><path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z" /></>,
    shield: <><path d="M12 3 20 6v5c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6l8-3Z" /><path d="m9 12 2 2 4-4" /></>,
    chart: <><path d="M4 19V5M4 19h17" /><path d="m7 15 4-4 3 2 6-7" /></>,
    warning: <><path d="m12 3 9 17H3L12 3Z" /><path d="M12 9v5M12 17h.01" /></>,
    truck: <><path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z" /><circle cx="7.5" cy="18" r="1.5" /><circle cx="18" cy="18" r="1.5" /></>,
    check: <><path d="M20 11.5V12a8 8 0 1 1-4.7-7.3" /><path d="m8 11 4 4L21 5" /></>,
    crane: <><path d="M3 20h18M7 20V5h2v15M8 5h12M16 5v3M12 8h8M19 8v3" /><path d="M18 11v5" /><path d="M16.5 16h3v2h-3z" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></>,
    bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></>,
    chevron: <path d="m7 10 5 5 5-5" />,
    arrow: <><path d="M7 17 17 7M7 7h10v10" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
    pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name] || paths.cube}</svg>;
}

function Panel({ title, subtitle, action, children, className = "" }) {
  return <section className={`panel ${className}`}>
    {(title || action) && <div className="panel-heading">
      <div>{title && <h2>{title}</h2>}{subtitle && <p>{subtitle}</p>}</div>
      {action}
    </div>}
    {children}
  </section>;
}

function Button({ children, kind = "secondary", onClick, icon, type = "button" }) {
  return <button className={`button ${kind}`} type={type} onClick={onClick}>{icon && <Icon name={icon} size={15} />}{children}</button>;
}

function StatCard({ label, value, delta, tone = "blue", icon }) {
  return <div className="stat-card">
    <div className="stat-top"><span>{label}</span><span className={`stat-icon ${tone}`}><Icon name={icon} size={17} /></span></div>
    <div className="stat-bottom"><strong>{value}</strong><span className={`delta ${delta.startsWith("-") ? "negative" : ""}`}>{delta}</span></div>
  </div>;
}

function Status({ children, tone = "blue" }) {
  return <span className={`status ${tone}`}><i />{children}</span>;
}

function TwinScene({ visibleLayers, onToggle, floor, onFloorChange }) {
  return <div className="twin-scene">
    <div className="scene-top">
      <div className="scene-live"><i /> LIVE MODEL <span>Updated 2 min ago</span></div>
      <label className="select-wrap"><span>Floor</span><select value={floor} onChange={(event) => onFloorChange(event.target.value)}><option>All floors</option><option>Floor 12</option><option>Floor 08</option><option>Floor 04</option><option>Ground</option></select><Icon name="chevron" size={13} /></label>
    </div>
    <div className="scene-canvas">
      <div className="scene-grid" />
      <div className="scene-sun" />
      <svg className="twin-building" viewBox="0 0 700 520" role="img" aria-label="Interactive 3D model of Aurora Tower construction site">
        <defs>
          <linearGradient id="glass" x1="0" x2="1" y1="0" y2="1"><stop stopColor="#52b9cf" stopOpacity=".78" /><stop offset=".48" stopColor="#26617e" stopOpacity=".8" /><stop offset="1" stopColor="#173a58" stopOpacity=".92" /></linearGradient>
          <linearGradient id="side" x1="0" x2="1"><stop stopColor="#193b5a" /><stop offset="1" stopColor="#102d49" /></linearGradient>
          <linearGradient id="ground" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#183a50" stopOpacity=".85" /><stop offset="1" stopColor="#0d2032" stopOpacity=".2" /></linearGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        <ellipse cx="350" cy="442" rx="275" ry="38" fill="#35b8c5" opacity=".08" />
        <path d="m105 412 242-140 240 140-242 91z" fill="url(#ground)" stroke="#4b8ea2" strokeOpacity=".5" />
        <path d="m152 409 195-112 194 112-196 73z" fill="#102b40" stroke="#347184" strokeOpacity=".65" />
        <path d="m242 356 120-69 124 72-122 71z" fill="#17344a" stroke="#5aa6b2" strokeOpacity=".48" />
        <g opacity={visibleLayers.structure ? 1 : .16}>
          <path d="m281 118 130 72v226l-130-73z" fill="url(#glass)" stroke="#7ee1dc" strokeWidth="1.5" />
          <path d="m411 190 96-55v223l-96 58z" fill="url(#side)" stroke="#59a9b5" strokeWidth="1.4" />
          <path d="m281 118 96-55 130 72-96 55z" fill="#357e8f" fillOpacity=".76" stroke="#75d9d4" strokeWidth="1.3" />
          {[0,1,2,3,4,5,6,7,8,9].map((n) => <g key={n}>
            <path d={`M281 ${141 + n * 21.5} 411 ${213 + n * 21.5} 507 ${158 + n * 21.5}`} fill="none" stroke={floor === "All floors" || floor === `Floor ${String(12 - n).padStart(2, "0")}` ? "#80e1d8" : "#488596"} strokeOpacity=".72" strokeWidth="1" />
            <path d={`M296 ${148 + n * 21.5}v70M326 ${165 + n * 21.5}v70M356 ${181 + n * 21.5}v70M386 ${198 + n * 21.5}v70`} stroke="#9ce7de" strokeOpacity=".3" strokeWidth="1" />
            <path d={`M430 ${201 + n * 21.5}l61-35`} stroke="#67bdc5" strokeOpacity=".38" strokeWidth="1" />
          </g>)}
          <path d="m281 118 0 226M411 190v226M507 135v223" stroke="#a3eee3" strokeOpacity=".8" />
        </g>
        {visibleLayers.equipment && <g stroke="#e8b866" strokeWidth="2" fill="none" opacity=".9">
          <path d="M208 327V85M193 85h115M208 94l84 0M292 94v51M207 327l-22 49M207 327l23 49" />
          <path d="m489 322 34-82 40 22M523 240l-9-5M561 262v65" />
        </g>}
        {visibleLayers.safety && <g filter="url(#glow)">
          <circle cx="458" cy="374" r="12" fill="#eeaf56" fillOpacity=".26" stroke="#f4b65d" /><circle cx="458" cy="374" r="3" fill="#ffc76d" />
          <circle cx="235" cy="398" r="12" fill="#55d5b1" fillOpacity=".23" stroke="#55d5b1" /><circle cx="235" cy="398" r="3" fill="#7cf0ca" />
          <circle cx="534" cy="370" r="12" fill="#55d5b1" fillOpacity=".23" stroke="#55d5b1" /><circle cx="534" cy="370" r="3" fill="#7cf0ca" />
        </g>}
        <g opacity=".8" fill="#2a6274" stroke="#5bb2b8">
          <path d="m133 397 30-17 30 18-31 18z" /><path d="m166 416 25-14 26 15-26 15z" />
          <path d="m532 401 27-16 30 18-28 17z" /><path d="m470 430 25-14 27 16-26 15z" />
        </g>
      </svg>
      <div className="scene-label label-tower"><i /> TOWER A <span>68% complete</span></div>
      <div className="scene-label label-risk"><i /> Safety zone <span>3 cameras active</span></div>
      <div className="scene-scale"><span>0</span><i /><span>20 m</span></div>
      <div className="scene-controls"><button aria-label="Zoom in">+</button><button aria-label="Zoom out">−</button><button aria-label="Reset view">⌂</button></div>
    </div>
    <div className="scene-legend">
      <span className="legend-heading">LAYERS</span>
      {[
        ["structure", "Structure", "teal"],
        ["equipment", "Equipment", "orange"],
        ["safety", "Safety zones", "green"],
      ].map(([key, label, color]) => <button key={key} className={`layer-toggle ${visibleLayers[key] ? "selected" : ""}`} onClick={() => onToggle(key)}><i className={color} />{label}<span>{visibleLayers[key] ? "On" : "Off"}</span></button>)}
      <span className="scene-legend-note"><i /> Model synced</span>
    </div>
  </div>;
}

function BIMPage() {
  const [layers, setLayers] = React.useState({ structure: true, equipment: true, safety: true });
  const [floor, setFloor] = React.useState("All floors");
  return <>
    <div className="stats-grid">
      <StatCard label="Overall progress" value="68.4%" delta="+2.4% this week" tone="blue" icon="chart" />
      <StatCard label="Active workers" value="248" delta="+18 on site" tone="green" icon="check" />
      <StatCard label="Open issues" value="12" delta="-3 this week" tone="orange" icon="warning" />
      <StatCard label="Schedule variance" value="2 days" delta="Ahead of schedule" tone="purple" icon="calendar" />
    </div>
    <div className="bim-layout">
      <Panel title="Aurora Tower · Digital Twin" subtitle="Central District, Yangon · Model version 2.8.4" className="twin-panel">
        <TwinScene visibleLayers={layers} onToggle={(layer) => setLayers((current) => ({ ...current, [layer]: !current[layer] }))} floor={floor} onFloorChange={setFloor} />
      </Panel>
      <div className="bim-side">
        <Panel title="Project health" subtitle="Live project overview" className="health-panel">
          <div className="health-score"><div className="score-ring"><strong>86</strong><small>/ 100</small></div><div><b>On track</b><span>Project performance</span><small><i /> Updated just now</small></div></div>
          <div className="health-list">
            <div><span>Schedule</span><strong>Good</strong><i className="good" /></div>
            <div><span>Budget</span><strong>On target</strong><i className="good" /></div>
            <div><span>Safety</span><strong>Needs attention</strong><i className="warn" /></div>
          </div>
        </Panel>
        <Panel title="Today's activity" subtitle="Wednesday, 19 November">
          <div className="activity-list">
            <div><i className="activity-dot green" /><p><b>Concrete pour completed</b><span>Level 08 · 10:42 AM</span></p><em>Done</em></div>
            <div><i className="activity-dot orange" /><p><b>Safety inspection flagged</b><span>East scaffold · 10:18 AM</span></p><em>Review</em></div>
            <div><i className="activity-dot blue" /><p><b>Steel delivery received</b><span>Loading bay · 09:36 AM</span></p><em>Logged</em></div>
          </div>
          <button className="text-button">View all activity <span>→</span></button>
        </Panel>
      </div>
    </div>
    <div className="bottom-grid">
      <Panel title="Milestone progress" subtitle="Construction schedule" action={<button className="text-button">View schedule →</button>}>
        <div className="milestone-items">
          {[
            ["Foundation", "Completed", 100, "green"],
            ["Structural frame", "In progress", 72, "blue"],
            ["Facade & glazing", "In progress", 36, "orange"],
          ].map(([name, status, percent, color]) => <div className="milestone" key={name}><div><b>{name}</b><span>{status}</span><strong>{percent}%</strong></div><i><em className={color} style={{ width: `${percent}%` }} /></i></div>)}
        </div>
      </Panel>
      <Panel title="AI site briefing" subtitle="A quick read of your project">
        <div className="briefing"><span className="brief-icon"><Icon name="spark" size={17} /></span><p>Work is progressing <b>2 days ahead of schedule</b>. One safety item needs attention at the East scaffold. Steel inventory is sufficient for the next 5 working days.</p><button aria-label="Open AI copilot" onClick={() => window.dispatchEvent(new CustomEvent("open-module", { detail: "copilot" }))}>Ask Copilot <span>→</span></button></div>
      </Panel>
    </div>
  </>;
}

function CopilotPage() {
  const [messages, setMessages] = React.useState([]);
  const [question, setQuestion] = React.useState("");
  const ask = (text) => {
    const prompt = text.trim();
    if (!prompt) return;
    setMessages((items) => [...items, { question: prompt, answer: "Based on the latest Aurora Tower project data, the team is 2 days ahead of schedule with 68.4% overall completion. I also found one safety item at the East scaffold that should be reviewed today." }]);
    setQuestion("");
  };
  return <div className="copilot-layout">
    <Panel title="Your construction copilot" subtitle="Ask questions about your project, reports, schedule, or site operations." className="copilot-chat">
      <div className="copilot-welcome"><div className="copilot-mark"><Icon name="spark" size={23} /></div><h3>Good morning, Alex</h3><p>I'm up to date with your project data. What would you like to know?</p></div>
      <div className="prompt-grid">{["What needs my attention today?", "Summarize this week's progress", "Are we on budget?", "Show open safety issues"].map((item) => <button key={item} onClick={() => ask(item)}>{item}<span>↗</span></button>)}</div>
      {messages.length > 0 && <div className="chat-messages">{messages.map((message, index) => <div className="chat-pair" key={`${message.question}-${index}`}><div className="user-message">{message.question}</div><div className="ai-message"><span className="ai-avatar"><Icon name="spark" size={14} /></span><p>{message.answer}</p></div></div>)}</div>}
      <form className="chat-form" onSubmit={(event) => { event.preventDefault(); ask(question); }}>
        <input aria-label="Ask the construction copilot" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about your project..." />
        <Button kind="primary" type="submit" icon="arrow">Send</Button>
      </form>
      <div className="privacy-note"><i /> Answers are grounded in your project data</div>
    </Panel>
    <div className="copilot-aside">
      <Panel title="Project context" subtitle="What Copilot knows">
        <div className="context-list"><div><Icon name="cube" /><span><b>Aurora Tower</b><small>Active project · Yangon</small></span></div><div><Icon name="calendar" /><span><b>Project schedule</b><small>Last synced 2 minutes ago</small></span></div><div><Icon name="chart" /><span><b>Cost reports</b><small>Updated this morning</small></span></div><div><Icon name="shield" /><span><b>Safety inspections</b><small>12 open items</small></span></div></div>
      </Panel>
      <Panel title="Recent insights" subtitle="Generated from your project">
        <div className="insight-list"><div><i className="insight-icon green"><Icon name="chart" size={15} /></i><p><b>Schedule is trending ahead</b><span>2 days ahead · Structural frame</span></p></div><div><i className="insight-icon orange"><Icon name="warning" size={15} /></i><p><b>Review East scaffold safety</b><span>1 high-priority observation</span></p></div><div><i className="insight-icon blue"><Icon name="truck" size={15} /></i><p><b>Steel supply looks healthy</b><span>5 working days of stock</span></p></div></div>
      </Panel>
    </div>
  </div>;
}

function SafetyPage() {
  const [filter, setFilter] = React.useState("All cameras");
  return <>
    <div className="stats-grid">
      <StatCard label="Safety score" value="92 / 100" delta="+4 this month" tone="green" icon="shield" />
      <StatCard label="Active cameras" value="18 / 20" delta="2 offline" tone="blue" icon="search" />
      <StatCard label="Open observations" value="7" delta="2 high priority" tone="orange" icon="warning" />
      <StatCard label="Days without incident" value="42" delta="Site record: 61 days" tone="purple" icon="calendar" />
    </div>
    <div className="content-grid two-col">
      <Panel title="AI camera monitoring" subtitle="Live safety coverage across your site" action={<select className="filter-select" value={filter} onChange={(event) => setFilter(event.target.value)}><option>All cameras</option><option>Active</option><option>Needs review</option></select>}>
        <div className="camera-grid">{[
          ["East scaffold", "CAM-04", "Review needed", "orange", "Scaffold guardrail check"],
          ["Main entrance", "CAM-01", "Live", "green", "PPE compliance 98%"],
          ["Loading bay", "CAM-08", "Live", "green", "PPE compliance 96%"],
          ["Level 08", "CAM-12", "Live", "green", "Area clear"],
        ].filter((camera) => filter === "All cameras" || filter === "Active" && camera[2] === "Live" || filter === "Needs review" && camera[2] === "Review needed").map((camera, index) => <div className="camera-card" key={camera[1]}><div className={`camera-preview preview-${index}`}><span className="camera-live"><i /> {camera[2] === "Live" ? "LIVE" : "REVIEW"}</span><div className="camera-scene"><i /><i /><i /><b /></div><span className="camera-time">10:4{index} AM</span></div><div className="camera-info"><div><b>{camera[0]}</b><span>{camera[1]}</span></div><Status tone={camera[3]}>{camera[2]}</Status></div><p>{camera[4]}</p></div>)}</div>
      </Panel>
      <Panel title="Recent observations" subtitle="AI-detected safety events" action={<button className="text-button">View all →</button>}>
        <div className="observation-list">{[
          ["High", "Guardrail gap detected", "East scaffold · Level 06", "10:18 AM", "orange"],
          ["Medium", "Worker PPE check", "Main entrance", "09:52 AM", "blue"],
          ["Low", "Restricted zone entry", "Loading bay", "09:14 AM", "green"],
          ["Resolved", "Trip hazard cleared", "Level 05 · West", "Yesterday", "green"],
        ].map((item) => <div className="observation" key={item[1]}><span className={`priority-mark ${item[4]}`}><Icon name={item[0] === "High" ? "warning" : "shield"} size={15} /></span><div><div><b>{item[1]}</b><Status tone={item[4]}>{item[0]}</Status></div><span>{item[2]}</span></div><time>{item[3]}</time></div>)}</div>
      </Panel>
    </div>
  </>;
}

function CostPage() {
  const costs = [["Labor", "$1.84M", "$2.40M", 77, "blue"], ["Materials", "$2.16M", "$3.10M", 70, "teal"], ["Equipment", "$640K", "$900K", 71, "purple"], ["Subcontractors", "$980K", "$1.60M", 61, "orange"]];
  return <>
    <div className="stats-grid">
      <StatCard label="Approved budget" value="$12.8M" delta="Project baseline" tone="blue" icon="chart" />
      <StatCard label="Committed cost" value="$8.42M" delta="65.8% of budget" tone="purple" icon="check" />
      <StatCard label="Actual spend" value="$6.21M" delta="Within plan" tone="green" icon="arrow" />
      <StatCard label="Forecast at completion" value="$12.4M" delta="$400K under budget" tone="orange" icon="calendar" />
    </div>
    <div className="content-grid two-col">
      <Panel title="Budget vs. actual" subtitle="Monthly cost performance · 2026" action={<select className="filter-select"><option>Year to date</option><option>Last 6 months</option><option>All time</option></select>}>
        <div className="chart-legend-row"><span><i className="legend-actual" />Actual spend</span><span><i className="legend-budget" />Planned budget</span></div>
        <div className="bar-chart"><div className="chart-y"><span>$1.6M</span><span>$1.2M</span><span>$800K</span><span>$400K</span><span>$0</span></div><div className="bar-chart-area"><div className="chart-lines"><i /><i /><i /><i /><i /></div><div className="bar-groups">{[["Jan", 42, 51], ["Feb", 50, 58], ["Mar", 47, 60], ["Apr", 66, 65], ["May", 58, 68], ["Jun", 70, 72], ["Jul", 62, 78], ["Aug", 74, 81], ["Sep", 80, 83], ["Oct", 72, 87], ["Nov", 76, 90], ["Dec", 0, 0]].map(([month, actual, planned]) => <div className="bar-group" key={month}><div className="bars"><i style={{ height: `${actual}%` }} /><i style={{ height: `${planned}%` }} /></div><span>{month}</span></div>)}</div></div></div>
      </Panel>
      <Panel title="Cost breakdown" subtitle="Spend by cost category">
        <div className="cost-total"><span>Total committed</span><strong>$8,420,000</strong><Status tone="green">Within budget</Status></div>
        <div className="cost-categories">{costs.map(([name, actual, budget, percent, color]) => <div className="cost-category" key={name}><div><span><i className={color} />{name}</span><strong>{actual}<small> / {budget}</small></strong></div><i className="category-track"><em className={color} style={{ width: `${percent}%` }} /></i></div>)}</div>
        <div className="cost-foot"><span>Remaining budget</span><b>$4.38M</b></div>
      </Panel>
    </div>
  </>;
}

function RiskPage() {
  return <>
    <div className="stats-grid">
      <StatCard label="Schedule confidence" value="84%" delta="+6% this month" tone="green" icon="chart" />
      <StatCard label="Predicted completion" value="18 Aug 2027" delta="2 days ahead" tone="blue" icon="calendar" />
      <StatCard label="Active risks" value="9" delta="3 need action" tone="orange" icon="warning" />
      <StatCard label="Potential delay" value="4.5 days" delta="Down 1.2 days" tone="purple" icon="clock" />
    </div>
    <div className="content-grid two-col">
      <Panel title="Schedule outlook" subtitle="AI forecast based on current progress and project risks" className="risk-chart-panel">
        <div className="forecast-summary"><div><span>Baseline finish</span><b>20 Aug 2027</b></div><div><span>Predicted finish</span><b className="positive">18 Aug 2027</b></div><div><span>Confidence</span><b>84%</b></div></div>
        <div className="forecast-chart"><div className="forecast-y"><span>100%</span><span>75%</span><span>50%</span><span>25%</span><span>0%</span></div><svg viewBox="0 0 700 240" preserveAspectRatio="none" aria-label="Schedule forecast chart"><path className="forecast-gridline" d="M0 10H700M0 65H700M0 120H700M0 175H700M0 230H700" /><path className="forecast-band" d="M0 215 C70 185 130 170 200 147 S330 120 400 100 S530 62 700 22 L700 57 C530 95 470 120 400 138 S260 166 200 181 S70 210 0 230Z" /><path className="forecast-plan" d="M0 220 C70 195 130 175 200 150 S330 115 400 95 S530 55 700 30" /><path className="forecast-actual" d="M0 220 C70 194 130 184 200 158 S315 133 360 112" /><path className="forecast-dot" d="M360 112a5 5 0 1 0 0 10a5 5 0 0 0 0-10" /></svg></div>
        <div className="forecast-x"><span>Nov '26</span><span>Feb '27</span><span>May '27</span><span>Aug '27</span></div>
        <div className="chart-legend-row"><span><i className="line-actual" />Actual progress</span><span><i className="line-plan" />Baseline</span><span><i className="line-range" />AI confidence range</span></div>
      </Panel>
      <Panel title="Top project risks" subtitle="Ranked by likelihood and impact" action={<button className="text-button">Risk register →</button>}>
        <div className="risk-list">{[
          ["High", "Steel delivery lead time", "Procurement", "Could delay facade work by 4 days", 82],
          ["High", "East scaffold access", "Safety", "Inspection sign-off still pending", 76],
          ["Medium", "Heavy rainfall forecast", "Weather", "Possible impact to exterior works", 54],
          ["Medium", "Electrical subcontractor", "Workforce", "Crew availability below plan", 46],
        ].map((risk) => <div className="risk-item" key={risk[1]}><div className="risk-item-top"><Status tone={risk[0] === "High" ? "orange" : "blue"}>{risk[0]} risk</Status><span>{risk[2]}</span></div><b>{risk[1]}</b><p>{risk[3]}</p><div className="risk-score"><i><em style={{ width: `${risk[4]}%` }} /></i><span>{risk[4]}% likelihood</span></div></div>)}</div>
      </Panel>
    </div>
  </>;
}

const initialOrders = [
  { id: "PO-2026-084", item: "Structural steel beams", vendor: "Mandalay Steel Co.", delivery: "21 Nov 2026", amount: "$186,400", status: "In transit", tone: "blue" },
  { id: "PO-2026-083", item: "Ready-mix concrete", vendor: "Golden River Concrete", delivery: "20 Nov 2026", amount: "$42,800", status: "Confirmed", tone: "green" },
  { id: "PO-2026-082", item: "Facade glazing panels", vendor: "Yangon Glass Works", delivery: "26 Nov 2026", amount: "$92,150", status: "Awaiting approval", tone: "orange" },
  { id: "PO-2026-081", item: "Electrical cable · 500m", vendor: "Brightline Supply", delivery: "18 Nov 2026", amount: "$18,600", status: "Delivered", tone: "green" },
  { id: "PO-2026-080", item: "Safety harnesses · 40", vendor: "SafeBuild Myanmar", delivery: "17 Nov 2026", amount: "$4,200", status: "Delivered", tone: "green" },
];

function ProcurementPage() {
  const [filter, setFilter] = React.useState("All orders");
  const shown = filter === "All orders" ? initialOrders : initialOrders.filter((order) => order.status === filter);
  return <>
    <div className="stats-grid">
      <StatCard label="Open purchase orders" value="24" delta="5 need approval" tone="blue" icon="truck" />
      <StatCard label="Committed spend" value="$2.18M" delta="68% of procurement plan" tone="purple" icon="chart" />
      <StatCard label="On-time delivery" value="94.2%" delta="+2.1% this quarter" tone="green" icon="check" />
      <StatCard label="Supplier issues" value="3" delta="1 requires attention" tone="orange" icon="warning" />
    </div>
    <Panel title="Purchase orders" subtitle="Track orders, deliveries, and approvals" className="table-panel" action={<Button kind="primary" icon="plus" onClick={() => window.alert("Purchase order creation will be available when procurement is connected to the backend.")}>New purchase order</Button>}>
      <div className="table-toolbar"><div className="filter-tabs">{["All orders", "Awaiting approval", "In transit", "Delivered"].map((item) => <button className={filter === item ? "active" : ""} key={item} onClick={() => setFilter(item)}>{item}</button>)}</div><button className="icon-button" aria-label="Search orders"><Icon name="search" /></button></div>
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>ORDER</th><th>MATERIAL / ITEM</th><th>SUPPLIER</th><th>EXPECTED DELIVERY</th><th>AMOUNT</th><th>STATUS</th><th /></tr></thead><tbody>{shown.map((order) => <tr key={order.id}><td className="mono">{order.id}</td><td><b>{order.item}</b></td><td>{order.vendor}</td><td>{order.delivery}</td><td className="amount">{order.amount}</td><td><Status tone={order.tone}>{order.status}</Status></td><td><button className="more-button" aria-label={`More actions for ${order.id}`}>···</button></td></tr>)}</tbody></table>{shown.length === 0 && <div className="empty-state">No orders in this category.</div>}</div>
      <div className="table-foot"><span>Showing {shown.length} of 24 purchase orders</span><div><button disabled>Previous</button><button className="current-page">1</button><button>2</button><button>3</button><button>Next</button></div></div>
    </Panel>
    <div className="bottom-grid">
      <Panel title="Upcoming deliveries" subtitle="Next 7 days">
        <div className="delivery-list"><div><span className="delivery-date"><b>20</b><small>NOV</small></span><p><b>Ready-mix concrete · 12 m³</b><span>Golden River Concrete · Loading bay</span></p><Status tone="green">Tomorrow</Status></div><div><span className="delivery-date"><b>21</b><small>NOV</small></span><p><b>Structural steel beams · 4 units</b><span>Mandalay Steel Co. · Gate 2</span></p><Status tone="blue">In transit</Status></div><div><span className="delivery-date"><b>26</b><small>NOV</small></span><p><b>Facade glazing panels · 28 units</b><span>Yangon Glass Works · Loading bay</span></p><Status tone="orange">On order</Status></div></div>
      </Panel>
      <Panel title="Supplier performance" subtitle="Top suppliers this quarter">
        <div className="supplier-list">{[["Mandalay Steel Co.", "98%", "MS"], ["Golden River Concrete", "96%", "GR"], ["Yangon Glass Works", "91%", "YG"]].map(([name, score, initials]) => <div key={name}><span className="supplier-avatar">{initials}</span><b>{name}</b><strong>{score}</strong><small>On-time</small></div>)}</div>
      </Panel>
    </div>
  </>;
}

function QualityPage({ project, api }) {
  const [filter, setFilter] = React.useState("all");
  const [inspections, setInspections] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [formOpen, setFormOpen] = React.useState(false);
  const [creating, setCreating] = React.useState(false);
  const [busyId, setBusyId] = React.useState("");
  const [rejectingId, setRejectingId] = React.useState("");
  const [rejectReason, setRejectReason] = React.useState("");
  const [form, setForm] = React.useState({
    inspection_code: `QC-${Date.now().toString().slice(-6)}`,
    title: "",
    inspection_type: "General",
    location: "",
    scheduled_on: "",
    finding_code: "ITEM-01",
    finding_description: "",
    result: "pass",
    severity: "minor",
    corrective_action: "",
  });

  const refresh = React.useCallback(async () => {
    if (!project) {
      setInspections([]);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const records = await api(`/projects/${project.id}/inspections?limit=200`);
      setInspections(records);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [api, project]);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const updateForm = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const createInspection = async (event) => {
    event.preventDefault();
    setCreating(true);
    setError("");
    const finding = {
      finding_code: form.finding_code,
      description: form.finding_description,
      result: form.result,
    };
    if (form.result === "fail") {
      finding.severity = form.severity;
      finding.corrective_action = form.corrective_action;
    }
    try {
      await api(`/projects/${project.id}/inspections`, {
        method: "POST",
        body: {
          inspection_code: form.inspection_code,
          title: form.title,
          inspection_type: form.inspection_type,
          location: form.location,
          scheduled_on: form.scheduled_on || null,
          findings: [finding],
        },
      });
      setFormOpen(false);
      setForm((current) => ({
        ...current,
        inspection_code: `QC-${Date.now().toString().slice(-6)}`,
        title: "",
        location: "",
        scheduled_on: "",
        finding_description: "",
        result: "pass",
        corrective_action: "",
      }));
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setCreating(false);
    }
  };

  const runAction = async (inspection, action, comments) => {
    setBusyId(inspection.id);
    setError("");
    try {
      if (action === "submit") {
        await api(`/projects/${project.id}/inspections/${inspection.id}/submit`, {
          method: "POST",
        });
      } else {
        await api(`/projects/${project.id}/inspections/${inspection.id}/decision`, {
          method: "POST",
          body: { decision: action, comments },
        });
        setRejectingId("");
        setRejectReason("");
      }
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyId("");
    }
  };

  const filtered = filter === "all"
    ? inspections
    : inspections.filter((inspection) => inspection.status === filter);
  const submittedCount = inspections.filter((inspection) => inspection.status === "submitted").length;
  const approvedCount = inspections.filter((inspection) => inspection.status === "approved").length;
  const rejectedCount = inspections.filter((inspection) => inspection.status === "rejected").length;
  const findingCount = inspections.reduce(
    (total, inspection) => total + inspection.findings.filter((finding) => finding.result === "fail").length,
    0,
  );
  const approvalRate = approvedCount + rejectedCount
    ? `${Math.round((approvedCount / (approvedCount + rejectedCount)) * 100)}%`
    : "—";
  const toneForStatus = {
    draft: "purple",
    submitted: "blue",
    approved: "green",
    rejected: "orange",
  };
  const labelForStatus = {
    draft: "Draft",
    submitted: "Awaiting review",
    approved: "Approved",
    rejected: "Rejected",
  };

  if (!project) {
    return <Panel title="Quality inspections" subtitle="Choose an accessible project to view its inspection log">
      <div className="empty-state">No project is available for this account.</div>
    </Panel>;
  }

  return <>
    <div className="stats-grid">
      <StatCard label="Inspection records" value={inspections.length} delta="Current project" tone="blue" icon="check" />
      <StatCard label="Awaiting review" value={submittedCount} delta="Submitted inspections" tone="purple" icon="calendar" />
      <StatCard label="Failed findings" value={findingCount} delta="Corrective action recorded" tone="orange" icon="warning" />
      <StatCard label="Approval rate" value={approvalRate} delta={`${approvedCount} approved · ${rejectedCount} rejected`} tone="green" icon="chart" />
    </div>
    <Panel
      title="Inspection log"
      subtitle={`${project.name} · Inspection findings and independent decisions`}
      className="table-panel"
      action={<Button kind="primary" icon="plus" onClick={() => setFormOpen((open) => !open)}>{formOpen ? "Close form" : "New inspection"}</Button>}
    >
      {error && <div className="api-error" role="alert">{error}<button onClick={() => setError("")} aria-label="Dismiss error">×</button></div>}
      {formOpen && <form className="inspection-form" onSubmit={createInspection}>
        <label className="form-field"><span>Inspection code</span><input name="inspection_code" value={form.inspection_code} onChange={updateForm} required maxLength={50} /></label>
        <label className="form-field"><span>Title</span><input name="title" value={form.title} onChange={updateForm} required maxLength={200} /></label>
        <label className="form-field"><span>Type</span><input name="inspection_type" value={form.inspection_type} onChange={updateForm} required maxLength={80} /></label>
        <label className="form-field"><span>Location</span><input name="location" value={form.location} onChange={updateForm} required maxLength={200} /></label>
        <label className="form-field"><span>Scheduled date</span><input name="scheduled_on" type="date" value={form.scheduled_on} onChange={updateForm} /></label>
        <label className="form-field"><span>Finding code</span><input name="finding_code" value={form.finding_code} onChange={updateForm} required maxLength={50} /></label>
        <label className="form-field form-field-wide"><span>Finding / acceptance criterion</span><input name="finding_description" value={form.finding_description} onChange={updateForm} required maxLength={2000} /></label>
        <label className="form-field"><span>Result</span><select name="result" value={form.result} onChange={updateForm}><option value="pass">Pass</option><option value="fail">Fail</option><option value="not_applicable">Not applicable</option></select></label>
        {form.result === "fail" && <>
          <label className="form-field"><span>Severity</span><select name="severity" value={form.severity} onChange={updateForm}><option value="minor">Minor</option><option value="major">Major</option><option value="critical">Critical</option></select></label>
          <label className="form-field form-field-wide"><span>Corrective action</span><input name="corrective_action" value={form.corrective_action} onChange={updateForm} required maxLength={2000} /></label>
        </>}
        <div className="form-actions"><Button type="submit" kind="primary">{creating ? "Saving..." : "Save draft"}</Button></div>
      </form>}
      <div className="table-toolbar">
        <div className="filter-tabs">{[
          ["all", "All inspections"],
          ["draft", "Draft"],
          ["submitted", "Awaiting review"],
          ["approved", "Approved"],
          ["rejected", "Rejected"],
        ].map(([value, label]) => <button className={filter === value ? "active" : ""} key={value} onClick={() => setFilter(value)}>{label}</button>)}</div>
        <button className="icon-button" aria-label="Refresh inspections" onClick={refresh}><Icon name="search" /></button>
      </div>
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>INSPECTION</th><th>LOCATION</th><th>FINDINGS</th><th>SCHEDULED</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>
        {filtered.map((inspection) => <tr key={inspection.id}>
          <td><span className="mono">{inspection.inspection_code}</span><b className="table-subtitle">{inspection.title}</b><small className="inspection-type">{inspection.inspection_type}</small></td>
          <td>{inspection.location}</td>
          <td><details className="finding-details"><summary>{inspection.findings.length} item{inspection.findings.length === 1 ? "" : "s"} · {inspection.findings.filter((finding) => finding.result === "fail").length} failed</summary><ul>{inspection.findings.map((finding) => <li key={finding.id}><b>{finding.finding_code} · {finding.result.replace("_", " ")}</b><span>{finding.description}</span>{finding.corrective_action && <small>Action: {finding.corrective_action}</small>}</li>)}</ul></details></td>
          <td>{inspection.scheduled_on ? new Date(`${inspection.scheduled_on}T00:00:00`).toLocaleDateString() : "—"}</td>
          <td><Status tone={toneForStatus[inspection.status]}>{labelForStatus[inspection.status]}</Status></td>
          <td className="inspection-actions">
            {inspection.status === "draft" && <button className="text-button" disabled={busyId === inspection.id} onClick={() => runAction(inspection, "submit")}>{busyId === inspection.id ? "Submitting…" : "Submit"}</button>}
            {inspection.status === "submitted" && (rejectingId === inspection.id
              ? <div className="reject-form"><input aria-label="Rejection reason" value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} placeholder="Reason for rejection" /><button className="text-button" disabled={busyId === inspection.id || !rejectReason.trim()} onClick={() => runAction(inspection, "rejected", rejectReason)}>Confirm</button><button className="text-button" onClick={() => { setRejectingId(""); setRejectReason(""); }}>Cancel</button></div>
              : <div className="review-actions"><button className="text-button" disabled={busyId === inspection.id} onClick={() => runAction(inspection, "approved")}>Approve</button><button className="text-button reject-link" onClick={() => setRejectingId(inspection.id)}>Reject</button></div>)}
            {inspection.decision?.comments && <small className="decision-note">{inspection.decision.comments}</small>}
          </td>
        </tr>)}
      </tbody></table>{loading && <div className="empty-state">Loading inspections…</div>}{!loading && filtered.length === 0 && <div className="empty-state">No inspections in this category.</div>}</div>
      <div className="table-foot"><span>Showing {filtered.length} of {inspections.length} inspection records</span><button className="text-button" onClick={refresh}>Refresh data <span>↻</span></button></div>
    </Panel>
  </>;
}

function EquipmentPage() {
  const [filter, setFilter] = React.useState("All equipment");
  const assets = [
    { name: "Tower Crane TC-01", type: "Liebherr 280 EC-H", location: "North zone · 48m", status: "Operating", tone: "green", utilization: 82, hours: "1,482 h", last: "Just now" },
    { name: "Tower Crane TC-02", type: "Potain MDT 219", location: "South zone · 36m", status: "Operating", tone: "green", utilization: 74, hours: "1,208 h", last: "1 min ago" },
    { name: "Excavator EX-03", type: "CAT 320 GC", location: "Basement · Zone B", status: "Idle", tone: "blue", utilization: 42, hours: "867 h", last: "3 min ago" },
    { name: "Concrete Pump CP-01", type: "Putzmeister 42m", location: "Loading bay", status: "Maintenance", tone: "orange", utilization: 61, hours: "994 h", last: "12 min ago" },
  ];
  const filtered = filter === "All equipment" ? assets : assets.filter((asset) => asset.status === filter);
  return <>
    <div className="stats-grid">
      <StatCard label="Connected assets" value="36 / 40" delta="4 offline" tone="blue" icon="crane" />
      <StatCard label="Operating now" value="24" delta="67% utilization" tone="green" icon="chart" />
      <StatCard label="Maintenance due" value="3" delta="1 overdue" tone="orange" icon="warning" />
      <StatCard label="Fuel efficiency" value="87%" delta="+3% this month" tone="purple" icon="check" />
    </div>
    <div className="content-grid two-col">
      <Panel title="Site equipment map" subtitle="Live asset positions · Aurora Tower site">
        <div className="equipment-map"><div className="map-grid" /><div className="map-site"><span className="map-road road-one" /><span className="map-road road-two" /><div className="map-building"><b>AURORA TOWER</b></div><div className="map-zone zone-a">ZONE A</div><div className="map-zone zone-b">ZONE B</div>{[["TC-01", "map-pin pin-one"], ["TC-02", "map-pin pin-two"], ["EX-03", "map-pin pin-three"], ["CP-01", "map-pin pin-four"]].map(([label, cls]) => <span className={cls} key={label}><Icon name={label.startsWith("TC") ? "crane" : "truck"} size={15} /><small>{label}</small></span>)}</div><div className="map-legend"><span><i className="green-dot" /> Operating</span><span><i className="orange-dot" /> Maintenance</span></div></div>
      </Panel>
      <Panel title="Equipment health" subtitle="Fleet health and utilization">
        <div className="fleet-score"><div className="fleet-ring"><strong>87%</strong></div><p><b>Fleet health</b><span>36 assets reporting</span><small>+3% from last month</small></p></div>
        <div className="health-list"><div><span>Operating</span><strong>24 assets</strong><i className="good" /></div><div><span>Idle</span><strong>9 assets</strong><i className="info" /></div><div><span>Maintenance</span><strong>3 assets</strong><i className="warn" /></div><div><span>Offline</span><strong>4 assets</strong><i className="bad" /></div></div>
      </Panel>
    </div>
    <Panel title="Connected equipment" subtitle="Telematics and IoT device status" className="table-panel equipment-table-panel">
      <div className="table-toolbar"><div className="filter-tabs">{["All equipment", "Operating", "Idle", "Maintenance"].map((item) => <button className={filter === item ? "active" : ""} key={item} onClick={() => setFilter(item)}>{item}</button>)}</div><button className="icon-button" aria-label="Search equipment"><Icon name="search" /></button></div>
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>ASSET</th><th>LOCATION</th><th>STATUS</th><th>UTILIZATION</th><th>ENGINE HOURS</th><th>LAST SIGNAL</th></tr></thead><tbody>{filtered.map((asset) => <tr key={asset.name}><td><div className="asset-name"><span><Icon name="crane" size={17} /></span><p><b>{asset.name}</b><small>{asset.type}</small></p></div></td><td>{asset.location}</td><td><Status tone={asset.tone}>{asset.status}</Status></td><td><div className="utilization"><i><em style={{ width: `${asset.utilization}%` }} /></i><span>{asset.utilization}%</span></div></td><td>{asset.hours}</td><td>{asset.last}</td></tr>)}</tbody></table>{filtered.length === 0 && <div className="empty-state">No equipment in this category.</div>}</div>
    </Panel>
  </>;
}

const pageDetails = {
  bim: ["3D BIM + Digital Twin", "A live view of your construction site and project performance.", "Last synced 2 min ago"],
  copilot: ["AI Construction Copilot", "Your project data, summarized and ready for questions.", "AI assistant online"],
  safety: ["Safety AI Monitoring", "Stay ahead of site hazards with AI-assisted monitoring.", "18 cameras connected"],
  cost: ["Cost & Budget Analytics", "Understand project spend and keep your budget on track.", "Financials updated today"],
  risk: ["Delay / Risk Prediction", "See schedule risks early and make informed decisions.", "Forecast refreshed today"],
  procurement: ["Procurement Management", "Manage purchase orders, suppliers, and upcoming deliveries.", "24 open purchase orders"],
  quality: ["Quality Inspection", "Track site inspections, corrective actions, and quality trends.", "5 inspections scheduled today"],
  equipment: ["Equipment IoT Tracking", "Monitor connected equipment, utilization, and maintenance.", "36 assets reporting"],
};

function LoginPage({ onLogin }) {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const session = await apiRequest("/auth/login", null, {
        method: "POST",
        body: { email, password },
      });
      onLogin(session);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return <main className="login-screen">
    <section className="login-card">
      <div className="login-brand"><span className="brand-symbol"><i /><i /><i /></span><span><b>APEXIVE<span>AI</span></b><small>CONSTRUCTION OS</small></span></div>
      <h1>Sign in to your workspace</h1>
      <p>Use your organization account to access project operations.</p>
      {error && <div className="api-error" role="alert">{error}</div>}
      <form onSubmit={submit}>
        <label className="form-field"><span>Email</span><input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label className="form-field"><span>Password</span><input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <Button type="submit" kind="primary">{loading ? "Signing in..." : "Sign in"}</Button>
      </form>
      <small className="login-note">Session tokens are held in memory and cleared when you sign out or close this page.</small>
    </section>
  </main>;
}

function App() {
  const [activeModule, setActiveModule] = React.useState("bim");
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);
  const [notice, setNotice] = React.useState("");
  const [session, setSession] = React.useState(null);
  const [projects, setProjects] = React.useState([]);
  const [selectedProjectId, setSelectedProjectId] = React.useState("");
  const [projectsError, setProjectsError] = React.useState("");
  const replaceTokens = React.useCallback((tokens) => {
    setSession((current) => current ? { ...current, ...tokens } : current);
  }, []);
  const api = React.useCallback(
    (path, options) => apiRequest(path, { ...session, onTokens: replaceTokens }, options),
    [replaceTokens, session],
  );
  React.useEffect(() => {
    let active = true;
    if (!session) {
      setProjects([]);
      setSelectedProjectId("");
      return () => { active = false; };
    }
    setProjectsError("");
    api("/projects")
      .then((items) => {
        if (!active) return;
        setProjects(items);
        setSelectedProjectId((current) =>
          items.some((project) => project.id === current) ? current : (items[0]?.id || ""),
        );
      })
      .catch((requestError) => {
        if (active) setProjectsError(requestError.message);
      });
    return () => { active = false; };
  }, [api, session]);

  const active = pageDetails[activeModule];
  const selectedProject = projects.find((project) => project.id === selectedProjectId) || null;
  React.useEffect(() => {
    const handleOpenModule = (event) => setActiveModule(event.detail);
    window.addEventListener("open-module", handleOpenModule);
    return () => window.removeEventListener("open-module", handleOpenModule);
  }, []);
  const changeModule = (id) => {
    setActiveModule(id);
    setMobileNavOpen(false);
    setNotice("");
  };
  const pages = {
    bim: <BIMPage />,
    copilot: <CopilotPage />,
    safety: <SafetyPage />,
    cost: <CostPage />,
    risk: <RiskPage />,
    procurement: <ProcurementPage />,
    quality: <QualityPage project={selectedProject} api={api} />,
    equipment: <EquipmentPage />,
  };
  if (!session) return <LoginPage onLogin={setSession} />;
  return <div className="app-shell">
    <aside className={`sidebar ${mobileNavOpen ? "open" : ""}`}>
      <button className="brand" onClick={() => changeModule("bim")} aria-label="ApexiveAI Construction OS home"><span className="brand-symbol"><i /><i /><i /></span><span><b>APEXIVE<span>AI</span></b><small>CONSTRUCTION OS</small></span></button>
      <div className="workspace-switch"><span className="workspace-logo">A</span><span><small>WORKSPACE</small><b>Apexive Construction</b></span><Icon name="chevron" size={14} /></div>
      <div className="nav-caption">WORKSPACE</div>
      <nav className="module-nav" aria-label="Main navigation">{modules.map((item, index) => <button key={item.id} className={`nav-item ${activeModule === item.id ? "active" : ""}`} onClick={() => changeModule(item.id)}><Icon name={item.icon} size={17} /><span>{item.label}</span>{index === 0 && <i className="nav-live" />}</button>)}</nav>
      <div className="sidebar-bottom"><div className="site-status"><i /><span><b>API session active</b><small>{projectsError ? "Project access unavailable" : "Signed in securely"}</small></span></div><button className="profile-button" onClick={() => setSession(null)}><span className="profile-avatar">{session.user.full_name.split(" ").map((part) => part[0]).slice(0, 2).join("").toUpperCase()}</span><span><b>{session.user.full_name}</b><small>Sign out</small></span><Icon name="chevron" size={14} /></button></div>
    </aside>
    {mobileNavOpen && <button className="mobile-backdrop" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)} />}
    <div className="main-area">
      <header className="topbar">
        <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}><Icon name="menu" /></button>
        <div className="top-project"><span className="project-breadcrumb">Projects</span><span className="breadcrumb-separator">/</span>{projects.length ? <select className="top-project-select" aria-label="Select project" value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select> : <b>{projectsError ? "Project access unavailable" : "No accessible project"}</b>}</div>
        <div className="top-actions"><button className="top-icon" aria-label="Search" onClick={() => setNotice("Search is ready to connect to your project data.")}><Icon name="search" /></button><button className="top-icon notification-button" aria-label="Notifications" onClick={() => setNotice("Notifications will load from project workflows.")}><Icon name="bell" /></button><span className="top-divider" /><button className="top-date" onClick={() => setSession(null)}>Sign out</button></div>
      </header>
      <main className="page-content">
        <div className="page-heading"><div><div className="eyebrow"><span>{selectedProject ? selectedProject.code : "PROJECT WORKSPACE"}</span><i />{selectedProject ? selectedProject.name : "SELECT AN ACCESSIBLE PROJECT"}</div><h1>{active[0]}</h1><p>{active[1]}</p></div><div className="heading-actions"><span className="sync-status"><i />{activeModule === "quality" ? "Connected to API" : active[2]}</span><Button kind="secondary" icon="calendar" onClick={() => setNotice("Project reporting is ready to connect to your backend.")}>Reports</Button><Button kind="primary" icon="plus" onClick={() => setNotice(activeModule === "quality" ? "Use New inspection in the inspection log to create a quality record." : "This action will be available when this workflow is connected to the backend.")}>Create new</Button></div></div>
        {projectsError && <div className="api-error" role="alert">Could not load projects: {projectsError}<button onClick={() => setProjectsError("")} aria-label="Dismiss error">×</button></div>}
        {notice && <div className="notice-banner"><span>{notice}</span><button aria-label="Dismiss notification" onClick={() => setNotice("")}>×</button></div>}
        {pages[activeModule]}
        <footer className="page-footer"><span>© 2026 ApexiveAI Construction OS</span><span>Quality inspections are API-backed; other modules remain demo views</span><button onClick={() => setNotice("Help center integration is coming soon.")}>Help & support</button></footer>
      </main>
    </div>
  </div>;
}

createRoot(document.getElementById("root")).render(<App />);
